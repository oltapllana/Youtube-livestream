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
        {
            "channel_id": 12,
            "title": "Joey Does Tech",
            "url": "https://www.youtube.com/watch?v=GCYaMTVXc_0",
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
          {
            "channel_id": 13,
            "title": "Astro Horizons",
            "url": "https://www.youtube.com/watch?v=4l4k_0e4h-s",
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
    description, uploader, view_count, channel_id, channel_url, or None on failure.
    """
    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "yt_dlp",
                "--dump-json",
                "--no-download",
                "--no-playlist",
                "--socket-timeout",
                "10",
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
            "duration": info.get("duration"),  # None for live streams
            "description": (info.get("description") or "")[:200],
            "uploader": info.get("uploader", ""),
            "view_count": info.get("view_count", 0),
            "channel_id": info.get("channel_id", ""),
            "channel_url": info.get("channel_url", ""),
        }
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp timed out for %s", url)
        return None
    except Exception as exc:
        logger.warning("yt-dlp error for %s: %s", url, exc)
        return None


def discover_channel_live_streams(channel_url: str, max_streams: int = 5, timeout: int = 20) -> List[Dict[str, Any]]:
    """
    Discover OTHER live streams from the same YouTube channel using yt-dlp.
    Returns a list of live stream dicts.
    """
    try:
        streams_url = f"{channel_url}/streams"

        result = subprocess.run(
            [
                "python",
                "-m",
                "yt_dlp",
                "--dump-json",
                "--no-download",
                "--playlist-end",
                str(max_streams),
                "--socket-timeout",
                "10",
                "--match-filter",
                "is_live",
                streams_url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            logger.debug(f"No additional live streams found on {channel_url}")
            return []

        discovered = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                info = json.loads(line)
                if info.get("is_live", False):
                    discovered.append(
                        {
                            "title": info.get("title", ""),
                            "url": f"https://www.youtube.com/watch?v={info.get('id', '')}",
                            "is_live": True,
                            "uploader": info.get("uploader", ""),
                            "view_count": info.get("view_count", 0),
                            "channel_id": info.get("channel_id", ""),
                            "channel_url": info.get("channel_url", ""),
                        }
                    )
            except json.JSONDecodeError:
                continue

        if discovered:
            logger.info(f"Discovered {len(discovered)} additional live stream(s) from {channel_url}")

        return discovered

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout discovering streams from {channel_url}")
        return []
    except Exception as exc:
        logger.debug(f"Could not discover streams from {channel_url}: {exc}")
        return []


# ── Instance Generator ──────────────────────────────────────────────────────

class InstanceGenerator:
    """
    Generates a complete scheduling-algorithm instance.
    """

    def __init__(self):
        self.streams = self._get_all_streams()
        self.category_scores = CATEGORY_SCORES
        # Cache keyed on URL so we don't probe the same stream twice
        self._probe_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        # Track discovered streams to avoid duplicates
        self._discovered_streams: List[Dict[str, Any]] = []

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

    def _discover_additional_streams(self) -> List[Dict[str, Any]]:
        """
        Discover additional live streams from the same channels as hardcoded streams.
        """
        KNOWN_CHANNELS = {
            "https://www.youtube.com/channel/UC3prwMn9aU2z5Y158ZdGyyA": "technology",  # Crux
            "https://www.youtube.com/channel/UCmk6ZFMy1CT80orXca4tKew": "technology",  # Financial Express
            "https://www.youtube.com/channel/UCkvW_7kp9LJrztmgA4q4bJQ": "technology",  # Sen
            "https://www.youtube.com/channel/UCetYFjkhf7S7LwiuJxeC28g": "technology",  # Dream Trips
            "https://www.youtube.com/@JoeyDoesTech": "technology",  # Joey Does Tech
            "https://www.youtube.com/channel/UCLA_DiR1FfKNvjuUpBHmylQ": "science",  # NASA
            "https://www.youtube.com/channel/UCOazV478JlUdvbBgFN4wWXA": "science",  # NASASpaceflight
            "https://www.youtube.com/channel/UC-QRPODUcdhXzXiOxsOaouA": "science",  # afarTV
            "https://www.youtube.com/channel/UCkWQ0gDr4bzT7Tu2xR_AV0Q": "science",  # Space Streams
            "https://www.youtube.com/channel/UC9c3bXN57i-FuKiPi5I3vhQ": "science",  # Frontiers of Infinity
            "https://www.youtube.com/channel/UCO-cfMjj6FM8WztlNSoVBGg": "science",  # Interstellar News Hub
            "https://www.youtube.com/@Astro.Horizons": "science",  # Astro Horizons
            "https://www.youtube.com/channel/UCMpn1qLudF-zb4M4bqxLIbw": "climate",  # I Love You Venice
        }

        discovered_streams = []
        seen_urls = {s["url"] for s in self.streams}

        logger.info(f"Discovering live streams from {len(KNOWN_CHANNELS)} known channels...")

        for channel_url, category in KNOWN_CHANNELS.items():
            try:
                logger.debug(f"Checking {channel_url} for additional live streams...")
                new_streams = discover_channel_live_streams(channel_url, max_streams=3, timeout=15)

                for new_stream in new_streams:
                    new_url = new_stream["url"]

                    if new_url in seen_urls:
                        logger.debug(f"Skipping duplicate: {new_url}")
                        continue

                    discovered_streams.append(
                        {
                            "channel_id": len(self.streams) + len(discovered_streams),
                            "title": new_stream["title"],
                            "url": new_url,
                            "category": category,
                        }
                    )
                    seen_urls.add(new_url)
                    logger.info(f"Discovered new {category} stream: {new_stream['title']}")

            except Exception as e:
                logger.warning(f"Failed to discover from {channel_url}: {e}")
                continue

        if discovered_streams:
            logger.info(f"Discovery complete: found {len(discovered_streams)} additional streams")
        else:
            logger.info("No additional live streams discovered")

        return discovered_streams

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

    # ── public API ──────────────────────────────────────────────────────

    def generate_instance(
        self,
        scheduling_params: Dict[str, Any],
        probe_streams: bool = True,
        discover_new_streams: bool = False,
    ) -> Dict[str, Any]:
        """
        Build a full instance JSON ready for the beam-search algorithm.
        """
        opening_time = scheduling_params["opening_time"]
        closing_time = scheduling_params["closing_time"]
        min_duration = scheduling_params["min_duration"]
        requested_channels = scheduling_params["channels_count"]

        # Start with hardcoded streams
        available_streams = self.streams.copy()

        # Safely extract filters (defensive)
        cat_filter = scheduling_params.get("category_filter") or []
        if isinstance(cat_filter, str):
            cat_filter = [cat_filter]
        if not isinstance(cat_filter, (list, tuple, set)):
            cat_filter = []

        chan_ids = scheduling_params.get("selected_channel_ids") or []
        if isinstance(chan_ids, int):
            chan_ids = [chan_ids]
        elif isinstance(chan_ids, str):
            try:
                parsed = json.loads(chan_ids)
                if isinstance(parsed, list):
                    chan_ids = parsed
                else:
                    chan_ids = [parsed]
            except Exception:
                chan_ids = [c.strip() for c in chan_ids.split(",") if c.strip()]
        if not isinstance(chan_ids, (list, tuple, set)):
            chan_ids = []

        chan_id_set = set()
        for x in chan_ids:
            try:
                chan_id_set.add(int(x))
            except Exception:
                continue

        # Apply requested category / channel filters (if provided)
        logger.info("Filtering — category_filter=%s, selected_channel_ids=%s", cat_filter, list(chan_id_set) if chan_id_set else [])
        if cat_filter:
            cat_set = set(map(str, cat_filter))
            available_streams = [s for s in available_streams if str(s.get("category")) in cat_set]
            logger.info("After category filter: %d streams", len(available_streams))
        if chan_id_set:
            available_streams = [s for s in available_streams if int(s.get("channel_id", -1)) in chan_id_set]
            logger.info("After channel filter: %d streams", len(available_streams))

        # Fallback: if filters result in zero streams, use all streams
        if not available_streams:
            logger.warning(
                "Category/channel filters produced 0 streams (cat=%s, chan=%s). Falling back to all streams.",
                cat_filter, list(chan_id_set) if chan_id_set else [],
            )
            available_streams = self.streams.copy()

        # Optionally discover additional live streams from the same channels
        if discover_new_streams and probe_streams:
            logger.info("Discovering additional live streams from channels...")
            discovered = self._discover_additional_streams()
            if discovered:
                logger.info(f"Found {len(discovered)} additional live stream(s)")
                available_streams.extend(discovered)
            else:
                logger.info("No additional live streams discovered")

        total_streams = len(available_streams)
        channels_count = max(1, min(requested_channels, total_streams))
        if requested_channels != channels_count:
            logger.warning(
                "Requested %s channels, but only %s streams available. Clamping.",
                requested_channels,
                total_streams,
            )

        selected_streams = available_streams[:channels_count]

        # Optionally probe each stream for real metadata
        stream_metadata: Dict[str, Optional[Dict[str, Any]]] = {}
        if probe_streams:
            for s in selected_streams:
                meta = self._probe(s["url"])
                stream_metadata[s["url"]] = meta
                if meta:
                    logger.info(
                        "Stream %s (%s) — live=%s, title=%s",
                        s.get("channel_id", "discovered"),
                        s["url"],
                        meta["is_live"],
                        meta["title"],
                    )
                else:
                    logger.warning(
                        "Could not probe stream %s (%s) — will use defaults",
                        s.get("channel_id", "discovered"),
                        s["url"],
                    )

        # Build channels
        channels = []
        for stream in selected_streams:
            meta = stream_metadata.get(stream["url"])
            channel = self._generate_channel(stream, opening_time, closing_time, min_duration, meta)
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
        title = (meta["title"] if meta else None) or stream["title"]
        url = stream["url"]

        programs = self._generate_programs(channel_id, title, category, url, opening_time, closing_time, min_duration, meta)
        return {"channel_id": channel_id, "channel_name": title, "programs": programs}

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
        Fill the [opening_time, closing_time) window with sequential programs for one channel.
        """
        programs: List[Dict[str, Any]] = []
        current_time = opening_time
        program_count = 0
        base_score = self.category_scores.get(category, 75)

        is_live = meta["is_live"] if meta else False
        live_bonus = 10 if is_live else 0

        while current_time < closing_time:
            remaining = closing_time - current_time
            if remaining < min_duration:
                break

            duration = min(min_duration + random.randint(0, 60), remaining)
            program_end = current_time + duration
            score = max(40, base_score + live_bonus + random.randint(-10, 10))

            programs.append(
                {
                    "program_id": f"{title}_program_{program_count}",
                    "start": current_time,
                    "end": program_end,
                    "genre": category,
                    "score": score,
                    "url": url,
                }
            )
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
            "total_streams": sum(len(YOUTUBE_STREAMS[c]) for c in YOUTUBE_STREAMS),
        }