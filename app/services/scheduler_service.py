"""
Scheduler service — orchestrates the full scheduling workflow:
1. Generate an instance JSON (probing YouTube live streams)
2. Save to input directory
3. Execute the Beam Search algorithm as a subprocess
4. Read the output and build the response
"""

import json
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.services.instance_generator import InstanceGenerator
from app.services.request_store import store, RequestStatus
from app.utils.file_handler import save_json, load_json, get_latest_output, get_latest_output_for_input
from app.utils.config import (
    DATA_INPUT_DIR,
    DATA_OUTPUT_DIR,
    ALGORITHM_DIR,
    ALGORITHM_SCRIPT,
    MAX_EXECUTION_TIME,
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for orchestrating scheduling operations."""

    def __init__(self):
        self.input_dir = DATA_INPUT_DIR
        self.output_dir = DATA_OUTPUT_DIR
        self.instance_generator = InstanceGenerator()

    # ── 1. Generate instance ────────────────────────────────────────────

    def generate_instance(
        self,
        scheduling_params: Dict[str, Any],
        probe_streams: bool = True,
        discover_new_streams: bool = False,
    ) -> Dict[str, Any]:
        """Build a full instance dict ready for the algorithm."""
        instance = self.instance_generator.generate_instance(
            scheduling_params,
            probe_streams=probe_streams,
            discover_new_streams=discover_new_streams,
        )
        return instance

    # ── 2. Save instance ────────────────────────────────────────────────

    def save_instance(self, instance: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Persist instance JSON and return the file path."""
        filepath = save_json(instance, self.input_dir, filename=filename)
        return filepath

    # ── 3. Execute algorithm ────────────────────────────────────────────

    def execute_algorithm(self, instance_file: str) -> Dict[str, Any]:
        """
        Run the beam-search algorithm on the saved instance file.
        The algorithm is executed as a subprocess with its cwd set to the
        algorithm directory so relative imports within the algorithm work.
        """
        try:
            logger.info("Running algorithm on %s …", instance_file)
            result = subprocess.run(
                [
                    "python",
                    str(ALGORITHM_SCRIPT),
                    "--input",
                    str(instance_file),
                ],
                capture_output=True,
                text=True,
                timeout=MAX_EXECUTION_TIME,
                cwd=str(ALGORITHM_DIR),          # algorithm uses relative paths
            )

            if result.returncode != 0:
                logger.error("Algorithm stderr: %s", result.stderr)
                return {
                    "status": "error",
                    "message": f"Algorithm failed: {result.stderr[:500]}",
                }

            logger.info("Algorithm stdout: %s", result.stdout[:500])
            return {
                "status": "success",
                "message": "Algorithm executed successfully",
                "stdout": result.stdout,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Algorithm timed out after {MAX_EXECUTION_TIME}s",
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Algorithm execution error: {exc}",
            }

    # ── 4. Read result ──────────────────────────────────────────────────

    def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the scheduling result.

        First checks the in-memory store.  If the algorithm wrote an output
        file (the most recent JSON in data/output), reads and returns that.
        """
        entry = store.get(request_id)
        if entry is None:
            return None

        if entry["status"] == RequestStatus.COMPLETED and entry["result"]:
            return entry["result"]

        if entry["status"] == RequestStatus.ERROR:
            return {"status": "error", "error": entry["error"]}

        return {"status": str(entry["status"]), "message": entry["message"]}

    def read_latest_output(self) -> Optional[Dict[str, Any]]:
        """Read the most recent algorithm output file (global)."""
        output_path = get_latest_output(self.output_dir)
        if output_path is None:
            return None
        return load_json(output_path)

    def read_output_for_input(self, input_file: str) -> Optional[Dict[str, Any]]:
        """Read the output file that corresponds to a specific input file."""
        output_path = get_latest_output_for_input(self.output_dir, Path(input_file))
        if output_path is None:
            return None
        return load_json(output_path)

    # ── 5. Full pipeline (called from background task) ──────────────────

    def run_pipeline(
        self,
        request_id: str,
        scheduling_params: Dict[str, Any],
        probe_streams: bool = True,
        discover_new_streams: bool = False,
    ) -> None:
        """
        End-to-end: generate → save → run algorithm → store result.
        Designed to be called inside a BackgroundTask so the POST returns
        immediately with the request_id.
        """
        try:
            # Step 1 — generate instance
            store.update_status(
                request_id,
                RequestStatus.GENERATING,
                progress=10,
                message="Probing YouTube streams and generating instance…",
            )
            instance = self.generate_instance(
                scheduling_params,
                probe_streams=probe_streams,
                discover_new_streams=discover_new_streams,
            )
            instance = self._apply_dynamic_params(instance, scheduling_params)
            store.set_instance(request_id, instance)

            # Step 2 — save
            store.update_status(
                request_id,
                RequestStatus.GENERATING,
                progress=30,
                message="Instance generated, saving to disk…",
            )
            filepath = self.save_instance(instance)
            store.set_input_file(request_id, str(filepath))

            # Step 3 — run algorithm
            store.update_status(
                request_id,
                RequestStatus.RUNNING,
                progress=50,
                message="Running beam-search algorithm…",
            )
            start_t = time.time()
            algo_result = self.execute_algorithm(str(filepath))
            elapsed = round(time.time() - start_t, 2)

            if algo_result["status"] != "success":
                store.set_error(request_id, algo_result["message"])
                return

            # Step 4 — read output
            store.update_status(
                request_id,
                RequestStatus.RUNNING,
                progress=90,
                message="Reading algorithm output…",
            )
            output_data = self.read_output_for_input(str(filepath))
            if output_data is None:
                store.set_error(request_id, "Algorithm produced no output file")
                return

            # Build the enriched result — attach YouTube URLs, genre, and channel names from the instance
            url_map = self._build_url_map(instance)
            genre_map = self._build_genre_map(instance)
            channel_name_map = self._build_channel_name_map(instance)
            scheduled = output_data.get("scheduled_programs", [])
            enriched_programs: List[Dict[str, Any]] = []
            for prog in scheduled:
                enriched = {**prog}
                ch_id = prog.get("channel_id")
                pid = prog.get("program_id")
                enriched["url"] = url_map.get((ch_id, pid), url_map.get((ch_id, None), ""))
                enriched["genre"] = genre_map.get((ch_id, pid), genre_map.get((ch_id, None), ""))
                enriched["channel_name"] = channel_name_map.get(ch_id, f"Channel {ch_id}")
                enriched_programs.append(enriched)

            result = {
                "status": "completed",
                "scheduled_programs": enriched_programs,
                "total_score": self._extract_score(output_data),
                "execution_time": elapsed,
                "channels_used": list({p["channel_id"] for p in scheduled}),
                "total_programs": len(scheduled),
            }
            store.set_result(request_id, result)

        except Exception as exc:
            logger.exception("Pipeline failed for request %s", request_id)
            store.set_error(request_id, str(exc))

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_url_map(instance: Dict[str, Any]) -> Dict:
        """
        Build a map of (channel_id, program_id) → youtube_url
        and (channel_id, None) → youtube_url  (fallback per channel).
        """
        url_map: Dict = {}
        for ch in instance.get("channels", []):
            ch_id = ch["channel_id"]
            for p in ch.get("programs", []):
                url_map[(ch_id, p["program_id"])] = p.get("url", "")
                url_map[(ch_id, None)] = p.get("url", "")   # fallback
        return url_map

    @staticmethod
    def _build_genre_map(instance: Dict[str, Any]) -> Dict:
        """
        Build a map of (channel_id, program_id) → genre
        and (channel_id, None) → genre  (fallback per channel).
        """
        genre_map: Dict = {}
        for ch in instance.get("channels", []):
            ch_id = ch["channel_id"]
            for p in ch.get("programs", []):
                genre_map[(ch_id, p["program_id"])] = p.get("genre", "")
                genre_map[(ch_id, None)] = p.get("genre", "")
        return genre_map

    @staticmethod
    def _build_channel_name_map(instance: Dict[str, Any]) -> Dict:
        """
        Build a map of channel_id → channel_name.
        """
        name_map: Dict = {}
        for ch in instance.get("channels", []):
            name_map[ch["channel_id"]] = ch.get("channel_name", f"Channel {ch['channel_id']}")
        return name_map

    @staticmethod
    def _extract_score(output: Dict[str, Any]) -> float:
        """Try to get total score from output; if not present, sum fitnesses."""
        if "total_score" in output:
            return output["total_score"]
        return sum(p.get("fitness", 0) for p in output.get("scheduled_programs", []))

    def _apply_dynamic_params(
        self,
        instance: Dict[str, Any],
        scheduling_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        avg_score = self._calculate_average_score(instance)
        shortest = self._calculate_shortest_duration(instance)

        min_duration_pct = scheduling_params.get("min_duration_pct")
        if min_duration_pct:
            instance["min_duration"] = max(1, self._pct_of(shortest, min_duration_pct))

        switch_penalty_pct = scheduling_params.get("switch_penalty_pct")
        if switch_penalty_pct:
            instance["switch_penalty"] = self._pct_of(avg_score, switch_penalty_pct)

        selected_categories = scheduling_params.get("category_filter") or []
        use_default_time_preferences = self._has_all_default_categories(selected_categories)

        if use_default_time_preferences:
            instance["time_preferences"] = self._build_default_time_preferences()
        else:
            instance["time_preferences"] = []

        return instance

    @staticmethod
    def _pct_of(value: float, pct: int) -> int:
        return max(0, round(value * (pct / 100.0)))

    @staticmethod
    def _calculate_average_score(instance: Dict[str, Any]) -> float:
        scores = [
            p.get("score", 0)
            for ch in instance.get("channels", [])
            for p in ch.get("programs", [])
        ]
        if not scores:
            return 0
        return sum(scores) / len(scores)

    @staticmethod
    def _calculate_shortest_duration(instance: Dict[str, Any]) -> int:
        durations = [
            (p.get("end", 0) - p.get("start", 0))
            for ch in instance.get("channels", [])
            for p in ch.get("programs", [])
            if "start" in p and "end" in p
        ]
        if not durations:
            return instance.get("min_duration", 0)
        return min(durations)

    @staticmethod
    def _build_default_time_preferences(
    ) -> List[Dict[str, Any]]:
        return [
            {
                "start": 480,
                "end": 720,
                "preferred_genre": "technology",
                "bonus": 4,
            },
            {
                "start": 720,
                "end": 960,
                "preferred_genre": "science",
                "bonus": 4,
            },
            {
                "start": 960,
                "end": 1200,
                "preferred_genre": "climate",
                "bonus": 4,
            },
        ]

    @staticmethod
    def _has_all_default_categories(categories: Any) -> bool:
        required = {"technology", "science", "climate"}
        if not isinstance(categories, (list, tuple, set)):
            return False
        selected = {str(category).lower() for category in categories}
        return required.issubset(selected)
