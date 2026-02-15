"""
API Routes for TV Scheduling Backend.

Endpoints:
  POST /schedule          — submit a scheduling request (returns request_id)
  GET  /schedule/{id}     — retrieve the generated schedule
  GET  /status/{id}       — check processing progress
  GET  /streams           — list all hardcoded YouTube live streams
  POST /schedule/sync     — synchronous version (waits for result)
  GET  /preferences       — load saved filter preferences
  POST /preferences       — save filter preferences
"""

import uuid
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.request_response import ScheduleRequest, ScheduleResponse, ScheduleStatus
from app.services.scheduler_service import SchedulerService
from app.services.request_store import store, RequestStatus
from app.services.instance_generator import InstanceGenerator
from app.utils.config import (
    BASE_DIR,
    DEFAULT_OPENING_TIME,
    DEFAULT_CLOSING_TIME,
    DEFAULT_MIN_DURATION,
    DEFAULT_CHANNELS_COUNT,
    DEFAULT_SWITCH_PENALTY,
    DEFAULT_TERMINATION_PENALTY,
    DEFAULT_MAX_CONSECUTIVE_GENRE,
)

logger = logging.getLogger(__name__)
router = APIRouter()
scheduler_service = SchedulerService()


# ── POST /schedule  (async — returns immediately) ──────────────────────────

@router.post("/schedule")
async def submit_schedule(
    request: Optional[ScheduleRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    probe: bool = Query(True, description="Probe YouTube streams for live status (slower but richer data)"),
    discover: bool = Query(False, description="Discover additional live streams from same channels (experimental)"),
):
    request_id = str(uuid.uuid4())

    if request:
        scheduling_params = {
            "opening_time": request.opening_time,
            "closing_time": request.closing_time,
            "min_duration": request.min_duration,
            "min_duration_pct": request.min_duration_pct,
            "channels_count": request.channels_count,
            "max_consecutive_genre": request.max_consecutive_genre,
            "switch_penalty": request.switch_penalty,
            "switch_penalty_pct": request.switch_penalty_pct,
            "termination_penalty": request.termination_penalty,
            "time_preferences": [tp.model_dump() for tp in request.time_preferences],
            "bonus_pct": request.bonus_pct,
            "category_filter": request.category_filter,
            "selected_channel_ids": request.selected_channel_ids,
        }
    else:
        scheduling_params = {
            "opening_time": DEFAULT_OPENING_TIME,
            "closing_time": DEFAULT_CLOSING_TIME,
            "min_duration": DEFAULT_MIN_DURATION,
            "min_duration_pct": None,
            "channels_count": DEFAULT_CHANNELS_COUNT,
            "max_consecutive_genre": DEFAULT_MAX_CONSECUTIVE_GENRE,
            "switch_penalty": DEFAULT_SWITCH_PENALTY,
            "switch_penalty_pct": None,
            "termination_penalty": DEFAULT_TERMINATION_PENALTY,
            "time_preferences": [],
            "bonus_pct": None,
            "category_filter": None,
            "selected_channel_ids": None,
        }

    store.create(request_id)
    background_tasks.add_task(
        scheduler_service.run_pipeline,
        request_id,
        scheduling_params,
        probe_streams=probe,
        discover_new_streams=discover,
    )

    return {
        "request_id": request_id,
        "status": "pending",
        "message": "Scheduling request accepted. Poll /api/status/{request_id} for progress.",
    }


# ── POST /schedule/sync  (waits for result) ───────────────────────────────

@router.post("/schedule/sync")
async def submit_schedule_sync(
    request: Optional[ScheduleRequest] = None,
    probe: bool = Query(True, description="Probe YouTube streams for live status"),
    discover: bool = Query(False, description="Discover additional live streams from same channels"),
):
    request_id = str(uuid.uuid4())

    if request:
        scheduling_params = {
            "opening_time": request.opening_time,
            "closing_time": request.closing_time,
            "min_duration": request.min_duration,
            "min_duration_pct": request.min_duration_pct,
            "channels_count": request.channels_count,
            "max_consecutive_genre": request.max_consecutive_genre,
            "switch_penalty": request.switch_penalty,
            "switch_penalty_pct": request.switch_penalty_pct,
            "termination_penalty": request.termination_penalty,
            "time_preferences": [tp.model_dump() for tp in request.time_preferences],
            "bonus_pct": request.bonus_pct,
            "category_filter": request.category_filter,
            "selected_channel_ids": request.selected_channel_ids,
        }
    else:
        scheduling_params = {
            "opening_time": DEFAULT_OPENING_TIME,
            "closing_time": DEFAULT_CLOSING_TIME,
            "min_duration": DEFAULT_MIN_DURATION,
            "min_duration_pct": None,
            "channels_count": DEFAULT_CHANNELS_COUNT,
            "max_consecutive_genre": DEFAULT_MAX_CONSECUTIVE_GENRE,
            "switch_penalty": DEFAULT_SWITCH_PENALTY,
            "switch_penalty_pct": None,
            "termination_penalty": DEFAULT_TERMINATION_PENALTY,
            "time_preferences": [],
            "bonus_pct": None,
            "category_filter": None,
            "selected_channel_ids": None,
        }

    store.create(request_id)
    scheduler_service.run_pipeline(request_id, scheduling_params, probe_streams=probe, discover_new_streams=discover)

    entry = store.get(request_id)
    if entry and entry["status"] == RequestStatus.COMPLETED:
        return {
            "request_id": request_id,
            **entry["result"],
        }
    else:
        error_msg = entry["error"] if entry else "Unknown error"
        raise HTTPException(status_code=500, detail=error_msg)


# ── GET /schedule/{request_id} ─────────────────────────────────────────────

@router.get("/schedule/{request_id}")
async def get_schedule(request_id: str):
    if not store.exists(request_id):
        raise HTTPException(status_code=404, detail="Request ID not found")

    entry = store.get(request_id)

    if entry["status"] == RequestStatus.COMPLETED:
        return {
            "request_id": request_id,
            **entry["result"],
        }

    if entry["status"] == RequestStatus.ERROR:
        raise HTTPException(
            status_code=500,
            detail=entry["error"] or "Algorithm failed",
        )

    return {
        "request_id": request_id,
        "status": entry["status"].value,
        "message": entry["message"],
    }


# ── GET /status/{request_id} ───────────────────────────────────────────────

@router.get("/status/{request_id}")
async def check_status(request_id: str):
    if not store.exists(request_id):
        raise HTTPException(status_code=404, detail="Request ID not found")

    entry = store.get(request_id)
    return {
        "request_id": request_id,
        "status": entry["status"].value,
        "progress": entry["progress"],
        "message": entry["message"],
    }


# ── GET /streams ────────────────────────────────────────────────────────────

@router.get("/streams")
async def list_streams(
    probe: bool = Query(False, description="Probe each URL with yt-dlp (slow, ~15 s per stream)"),
):
    if probe:
        gen = InstanceGenerator()
        return {"streams": gen.probe_all_streams()}
    return InstanceGenerator.get_all_streams_info()


# ── Preferences ─────────────────────────────────────────────────────────────

PREFS_FILE = BASE_DIR / "user_preferences.json"

DEFAULT_PREFERENCES = {
    "opening_time": DEFAULT_OPENING_TIME,
    "closing_time": DEFAULT_CLOSING_TIME,
    "min_duration": DEFAULT_MIN_DURATION,
    "min_duration_pct": None,
    "channels_count": DEFAULT_CHANNELS_COUNT,
    "switch_penalty": DEFAULT_SWITCH_PENALTY,
    "switch_penalty_pct": None,
    "termination_penalty": DEFAULT_TERMINATION_PENALTY,
    "max_consecutive_genre": DEFAULT_MAX_CONSECUTIVE_GENRE,
    "time_preferences": [],
    "bonus_pct": None,
    "category_filter": [],
    "selected_channel_ids": [],
}


class UserPreferences(BaseModel):
    opening_time: int = Field(default=480, description="Opening time (minutes from midnight)")
    closing_time: int = Field(default=1380, description="Closing time (minutes from midnight)")
    min_duration: Optional[int] = Field(default=30, description="Minimum program duration in minutes")
    min_duration_pct: Optional[int] = Field(default=100, description="Min duration % of shortest program")
    channels_count: int = Field(default=10, description="Number of channels (10 or 20)")
    switch_penalty: Optional[int] = Field(default=10)
    switch_penalty_pct: Optional[int] = Field(default=10, description="Switch penalty % of average score")
    termination_penalty: int = Field(default=20)
    max_consecutive_genre: int = Field(default=2)
    bonus_pct: Optional[int] = Field(default=5, description="Time preference bonus % of average score")
    category_filter: Optional[List[str]] = Field(default_factory=list, description="Selected categories")
    selected_channel_ids: Optional[List[int]] = Field(default_factory=list, description="Selected channel IDs")


@router.get("/preferences")
async def get_preferences():
    if PREFS_FILE.exists():
        with open(PREFS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_PREFERENCES


@router.post("/preferences")
async def save_preferences(prefs: UserPreferences):
    data = prefs.model_dump()
    with open(PREFS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "saved", "preferences": data}