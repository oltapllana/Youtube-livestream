"""
Instance Generator - Fetches real YouTube live stream info and converts
scheduling parameters + streams into a complete JSON instance for the algorithm.
"""

from typing import Dict, List, Any, Optional
import random
import logging
import subprocess
import json

logger = logging.getLogger(__name__)


# ── Hardcoded YouTube live-stream database ──────────────────────────────────
# Each entry is a known 24/7 or recurring live stream.
# The generator will probe each URL with yt-dlp to check if it's actually live.
YOUTUBE_STREAMS = {
    "technology": [
        {
            "channel_id": 0,
            "title": "Crux",
            "url": "https://www.youtube.com/watch?v=oXsBLbUUe3c",
            "category": "technology",
        },
        {
            "channel_id": 1,
            "title": "The Financial Express",
            "url": "https://www.youtube.com/watch?v=Gh1Mt4BSo6Y",
            "category": "technology",
        },
        {
            "channel_id": 2,
            "title": "Sen",
            "url": "https://www.youtube.com/watch?v=fO9e9jnhYK8",
            "category": "technology",
        },
        {
            "channel_id": 3,
            "title": "Dream Trips",
            "url": "https://www.youtube.com/watch?v=kWRhLLbLFE0",
            "category": "technology",
        },
    ],
    "science": [
        {
            "channel_id": 4,
            "title": "NASA",
            "url": "https://www.youtube.com/watch?v=xCrPD7tfcr0",
            "category": "science",
        },
        {
            "channel_id": 5,
            "title": "NASASpaceflight",
            "url": "https://www.youtube.com/watch?v=Jm8wRjD3xVA",
            "category": "science",
        },
        {
            "channel_id": 6,
            "title": "afarTV",
            "url": "https://www.youtube.com/watch?v=vytmBNhc9ig",
            "category": "science",
        },
        {
            "channel_id": 7,
            "title": "Space Streams",
            "url": "https://www.youtube.com/watch?v=nRkpb2NWn_4",
            "category": "science",
        },
        {
            "channel_id": 8,
            "title": "Frontiers of Infinity",
            "url": "https://www.youtube.com/watch?v=RwQPMHZHsY0",
            "category": "science",
        },
        {
            "channel_id": 9,
            "title": "Interstellar News Hub",
            "url": "http://youtube.com/watch?v=itx0IXjGEyQ",
            "category": "science",
        },
    ],
    "climate": [
        {
            "channel_id": 10,
            "title": "Interstellar News Hub (Climate)",
            "url": "https://www.youtube.com/watch?v=ToUVD_JdKvM",
            "category": "climate",
        },
        {
            "channel_id": 11,
            "title": "I love You Venice",
            "url": "https://www.youtube.com/watch?v=z7SiAaN4ogw",
            "category": "climate",
        },
    ],
}

# Base score per category – used when generating program scores
CATEGORY_SCORES = {
    "technology": 75,
    "science": 85,
    "climate": 78,
}


# ── YouTube live-stream probing ─────────────────────────────────────────────

def probe_youtube_stream(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    Use yt-dlp to extract metadata for a YouTube URL.
    Returns a dict with title, is_live, duration (seconds or None for live),
    description, uploader, view_count, or None on failure.
    """
    try:
        result = subprocess.run(
            [
                "python", "-m", "yt_dlp",
                "--dump-json",
                "--no-download",
                "--no-playlist",
                "--socket-timeout", "10",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning("yt-dlp failed for %s: %s", url, result.stderr[:200])
            return None

        info = json.loads(result.stdout)
        return {
            "title": info.get("title", ""),
            "is_live": info.get("is_live", False),
            "duration": info.get("duration"),          # None for live streams
            "description": (info.get("description") or "")[:200],
            "uploader": info.get("uploader", ""),
            "view_count": info.get("view_count", 0),
        }
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp timed out for %s", url)
        return None
    except Exception as exc:
        logger.warning("yt-dlp error for %s: %s", url, exc)
        return None


# ── Instance Generator ──────────────────────────────────────────────────────

class InstanceGenerator:
    """
    Generates a complete scheduling-algorithm instance.

    Workflow:
    1. Probes each hardcoded YouTube URL to check liveness / get real titles.
    2. Builds channels with sequential program slots that fill the time window.
    3. Attaches the YouTube URL to every program so the frontend can play it.
    """

    def __init__(self):
        self.streams = self._get_all_streams()
        self.category_scores = CATEGORY_SCORES
        # Cache keyed on URL so we don't probe the same stream twice
        self._probe_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_all_streams() -> List[Dict[str, Any]]:
        all_streams: List[Dict[str, Any]] = []
        for cat in ("technology", "science", "climate"):
            all_streams.extend(YOUTUBE_STREAMS[cat])
        return all_streams

    def _probe(self, url: str) -> Optional[Dict[str, Any]]:
        """Probe a URL (with caching)."""
        if url not in self._probe_cache:
            self._probe_cache[url] = probe_youtube_stream(url)
        return self._probe_cache[url]

    # ── public API ──────────────────────────────────────────────────────

    def generate_instance(
        self,
        scheduling_params: Dict[str, Any],
        probe_streams: bool = True,
    ) -> Dict[str, Any]:
        """
        Build a full instance JSON ready for the beam-search algorithm.

        Args:
            scheduling_params: dict with opening_time, closing_time,
                min_duration, channels_count, etc.
            probe_streams: if True, call yt-dlp for each stream to get
                real metadata and live status.  Set False for fast/offline mode.

        Returns:
            Instance dict (same schema the algorithm parser expects).
        """
        opening_time = scheduling_params["opening_time"]
        closing_time = scheduling_params["closing_time"]
        min_duration = scheduling_params["min_duration"]
        requested_channels = scheduling_params["channels_count"]
        total_streams = len(self.streams)
        channels_count = max(1, min(requested_channels, total_streams))
        if requested_channels != channels_count:
            logger.warning(
                "Requested %s channels, but only %s streams available. Clamping.",
                requested_channels,
                total_streams,
            )

        selected_streams = self.streams[:channels_count]

        # Optionally probe each stream for real metadata
        stream_metadata: Dict[str, Optional[Dict[str, Any]]] = {}
        if probe_streams:
            for s in selected_streams:
                meta = self._probe(s["url"])
                stream_metadata[s["url"]] = meta
                if meta:
                    logger.info(
                        "Stream %s (%s) — live=%s, title=%s",
                        s["channel_id"],
                        s["url"],
                        meta["is_live"],
                        meta["title"],
                    )
                else:
                    logger.warning(
                        "Could not probe stream %s (%s) — will use defaults",
                        s["channel_id"],
                        s["url"],
                    )

        # Build channels
        channels = []
        for stream in selected_streams:
            meta = stream_metadata.get(stream["url"])
            channel = self._generate_channel(
                stream, opening_time, closing_time, min_duration, meta
            )
            channels.append(channel)

        instance = {
            "opening_time": opening_time,
            "closing_time": closing_time,
            "min_duration": min_duration,
            "max_consecutive_genre": scheduling_params.get("max_consecutive_genre", 2),
            "channels_count": channels_count,
            "switch_penalty": scheduling_params.get("switch_penalty", 10),
            "termination_penalty": scheduling_params.get("termination_penalty", 20),
            "priority_blocks": scheduling_params.get("priority_blocks", []),
            "time_preferences": scheduling_params.get("time_preferences", []),
            "channels": channels,
        }
        return instance

    def probe_all_streams(self) -> List[Dict[str, Any]]:
        """
        Probe every hardcoded stream and return enriched info.
        Useful for the GET /api/streams endpoint.
        """
        results = []
        for stream in self.streams:
            meta = self._probe(stream["url"])
            entry = {**stream, "probed": meta is not None}
            if meta:
                entry["live_title"] = meta["title"]
                entry["is_live"] = meta["is_live"]
                entry["uploader"] = meta["uploader"]
                entry["view_count"] = meta["view_count"]
            results.append(entry)
        return results

    # ── private ─────────────────────────────────────────────────────────

    def _generate_channel(
        self,
        stream: Dict[str, Any],
        opening_time: int,
        closing_time: int,
        min_duration: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        channel_id = stream["channel_id"]
        category = stream["category"]
        # If we probed successfully, use the real title; otherwise fall back
        title = (meta["title"] if meta else None) or stream["title"]
        url = stream["url"]

        programs = self._generate_programs(
            channel_id, title, category, url, opening_time, closing_time, min_duration, meta
        )
        return {
            "channel_id": channel_id,
            "channel_name": title,
            "programs": programs,
        }

    def _generate_programs(
        self,
        channel_id: int,
        title: str,
        category: str,
        url: str,
        opening_time: int,
        closing_time: int,
        min_duration: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fill the [opening_time, closing_time) window with sequential programs
        for one channel.  Each program carries the YouTube URL so the frontend
        knows what to play.

        If the stream is detected as live (via probe), the score gets a bonus.
        """
        programs: List[Dict[str, Any]] = []
        current_time = opening_time
        program_count = 0
        base_score = self.category_scores.get(category, 75)

        # Live streams get a score boost (they're actually broadcasting)
        is_live = meta["is_live"] if meta else False
        live_bonus = 10 if is_live else 0

        while current_time < closing_time:
            remaining = closing_time - current_time
            if remaining < min_duration:
                break

            duration = min(min_duration + random.randint(0, 60), remaining)
            program_end = current_time + duration
            score = max(40, base_score + live_bonus + random.randint(-10, 10))

            programs.append({
                "program_id": f"{title}_program_{program_count}",
                "start": current_time,
                "end": program_end,
                "genre": category,
                "score": score,
                "url": url,
            })
            current_time = program_end
            program_count += 1

        return programs

    # ── static helpers ──────────────────────────────────────────────────

    @staticmethod
    def get_all_streams_info() -> Dict[str, Any]:
        """Return the raw hardcoded stream database."""
        return {
            "technology": YOUTUBE_STREAMS["technology"],
            "science": YOUTUBE_STREAMS["science"],
            "climate": YOUTUBE_STREAMS["climate"],
            "total_streams": sum(
                len(YOUTUBE_STREAMS[c]) for c in YOUTUBE_STREAMS
            ),
        }
