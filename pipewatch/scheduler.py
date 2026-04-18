"""Scheduled pipeline check runner for pipewatch."""

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class ScheduledJob:
    pipeline_name: str
    interval_seconds: int
    callback: Callable[[str], None]
    last_run: float = field(default=0.0)
    enabled: bool = True

    def is_due(self, now: float) -> bool:
        return self.enabled and (now - self.last_run) >= self.interval_seconds


class Scheduler:
    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def add_job(self, pipeline_name: str, interval_seconds: int, callback: Callable[[str], None]) -> None:
        self._jobs[pipeline_name] = ScheduledJob(
            pipeline_name=pipeline_name,
            interval_seconds=interval_seconds,
            callback=callback,
        )

    def remove_job(self, pipeline_name: str) -> bool:
        if pipeline_name in self._jobs:
            del self._jobs[pipeline_name]
            return True
        return False

    def list_jobs(self) -> List[str]:
        return list(self._jobs.keys())

    def _tick(self) -> None:
        while self._running:
            now = time.time()
            for job in list(self._jobs.values()):
                if job.is_due(now):
                    job.last_run = now
                    try:
                        job.callback(job.pipeline_name)
                    except Exception:
                        pass
            time.sleep(1)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._tick, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
