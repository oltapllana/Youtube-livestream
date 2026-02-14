"""
In-memory request store — tracks scheduling jobs and their results.

In production this would be Redis / a database.  For now a simple dict is fine.
"""

import threading
from typing import Dict, Any, Optional
from enum import Enum


class RequestStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"      # building instance / probing streams
    RUNNING = "running"            # algorithm executing
    COMPLETED = "completed"
    ERROR = "error"


class RequestStore:
    """Thread-safe in-memory store for scheduling requests."""

    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}

    # ── write ───────────────────────────────────────────────────────────

    def create(self, request_id: str) -> None:
        with self._lock:
            self._store[request_id] = {
                "status": RequestStatus.PENDING,
                "progress": 0,
                "message": "Request received",
                "result": None,
                "error": None,
                "instance": None,
                "input_file": None,
            }

    def update_status(
        self,
        request_id: str,
        status: RequestStatus,
        progress: int = 0,
        message: str = "",
    ) -> None:
        with self._lock:
            if request_id in self._store:
                self._store[request_id]["status"] = status
                self._store[request_id]["progress"] = progress
                self._store[request_id]["message"] = message

    def set_result(self, request_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            if request_id in self._store:
                self._store[request_id]["result"] = result
                self._store[request_id]["status"] = RequestStatus.COMPLETED
                self._store[request_id]["progress"] = 100
                self._store[request_id]["message"] = "Schedule generated successfully"

    def set_error(self, request_id: str, error: str) -> None:
        with self._lock:
            if request_id in self._store:
                self._store[request_id]["error"] = error
                self._store[request_id]["status"] = RequestStatus.ERROR
                self._store[request_id]["message"] = error

    def set_instance(self, request_id: str, instance: Dict[str, Any]) -> None:
        with self._lock:
            if request_id in self._store:
                self._store[request_id]["instance"] = instance

    def set_input_file(self, request_id: str, path: str) -> None:
        with self._lock:
            if request_id in self._store:
                self._store[request_id]["input_file"] = path

    # ── read ────────────────────────────────────────────────────────────

    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(request_id)

    def exists(self, request_id: str) -> bool:
        with self._lock:
            return request_id in self._store


# Singleton used across the app
store = RequestStore()
