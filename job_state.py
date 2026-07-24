import threading
import time
from collections import OrderedDict
from typing import Any


class GenerationCancelled(RuntimeError):
    pass


class JobStore:
    def __init__(self, max_jobs: int = 100, max_logs: int = 100, ttl_seconds: int = 21600):
        self.max_jobs = max_jobs
        self.max_logs = max_logs
        self.ttl_seconds = ttl_seconds
        self._jobs: dict[str, dict[str, Any]] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._lock = threading.RLock()

    def create(self, job_id: str, **fields) -> dict:
        now = time.time()
        with self._lock:
            self.cleanup(now)
            self._jobs[job_id] = {
                "status": "queued",
                "progress": 0,
                "logs": [],
                "created_at": now,
                "updated_at": now,
                **fields,
            }
            self._cancel_events[job_id] = threading.Event()
            self._trim_overflow(current=now)
            return dict(self._jobs[job_id])

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def all(self) -> dict[str, dict]:
        with self._lock:
            return {job_id: dict(job) for job_id, job in self._jobs.items()}

    def update(self, job_id: str, **fields) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields, updated_at=time.time())

    def log(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job["logs"] = [*job.get("logs", []), message][-self.max_logs:]
            job["updated_at"] = time.time()

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            event = self._cancel_events.get(job_id)
            if not job or not event or job["status"] in {"done", "error", "cancelled"}:
                return False
            event.set()
            if job.get("status") == "queued":
                job.update(status="cancelled", updated_at=time.time())
            else:
                job.update(status="cancelling", updated_at=time.time())
            return True

    def raise_if_cancelled(self, job_id: str) -> None:
        with self._lock:
            event = self._cancel_events.get(job_id)
        if event and event.is_set():
            raise GenerationCancelled("Generation cancelled by user")

    def cleanup(self, now: float | None = None) -> None:
        current = now or time.time()
        with self._lock:
            expired = [
                job_id
                for job_id, job in self._jobs.items()
                if current - job.get("updated_at", current) > self.ttl_seconds
            ]
            for job_id in expired:
                self._jobs.pop(job_id, None)
                self._cancel_events.pop(job_id, None)

            self._trim_overflow(current)

    def _trim_overflow(self, current: float) -> None:
        overflow = len(self._jobs) - self.max_jobs
        if overflow <= 0:
            return
        oldest = sorted(
            self._jobs,
            key=lambda job_id: self._jobs[job_id].get("updated_at", current),
        )
        for job_id in oldest[:overflow]:
            self._jobs.pop(job_id, None)
            self._cancel_events.pop(job_id, None)


class TtsCache:
    def __init__(self, max_entries: int = 3, max_bytes: int = 128 * 1024 * 1024):
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self._items: OrderedDict[tuple, tuple[Any, int]] = OrderedDict()
        self._bytes = 0
        self._lock = threading.RLock()

    def get(self, key: tuple):
        with self._lock:
            item = self._items.pop(key, None)
            if item is None:
                return None
            self._items[key] = item
            return item[0]

    def put(self, key: tuple, value) -> None:
        size = int(getattr(value[0], "nbytes", 0))
        if size > self.max_bytes:
            return
        with self._lock:
            previous = self._items.pop(key, None)
            if previous:
                self._bytes -= previous[1]
            self._items[key] = (value, size)
            self._bytes += size
            while len(self._items) > self.max_entries or self._bytes > self.max_bytes:
                _, (_, removed_size) = self._items.popitem(last=False)
                self._bytes -= removed_size
