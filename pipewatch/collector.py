"""Metrics collector for pipewatch."""
from collections import deque
from typing import Dict, Deque, Optional, List
from datetime import datetime
from pipewatch.metrics import PipelineMetric, compute_status


class MetricsCollector:
    """Collects and stores pipeline metric snapshots."""

    def __init__(self, max_history: int = 50):
        self._max_history = max_history
        self._store: Dict[str, Deque[PipelineMetric]] = {}

    def record(
        self,
        pipeline_id: str,
        duration_seconds: float = 0.0,
        error_count: int = 0,
        rows_processed: int = 0,
        timestamp: Optional[datetime] = None,
    ) -> PipelineMetric:
        """Record a new metric snapshot and return it."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        status = compute_status(duration_seconds=duration_seconds, error_count=error_count)
        metric = PipelineMetric(
            pipeline_id=pipeline_id,
            timestamp=timestamp,
            duration_seconds=duration_seconds,
            error_count=error_count,
            rows_processed=rows_processed,
            status=status,
        )
        if pipeline_id not in self._store:
            self._store[pipeline_id] = deque(maxlen=self._max_history)
        self._store[pipeline_id].append(metric)
        return metric

    def latest(self, pipeline_id: str) -> Optional[PipelineMetric]:
        """Return the most recent metric for a pipeline, or None."""
        queue = self._store.get(pipeline_id)
        if not queue:
            return None
        return queue[-1]

    def history(self, pipeline_id: str) -> List[PipelineMetric]:
        """Return full history for a pipeline."""
        return list(self._store.get(pipeline_id, []))

    def pipelines(self) -> List[str]:
        """Return all tracked pipeline IDs."""
        return list(self._store.keys())

    def clear(self, pipeline_id: str) -> None:
        """Clear history for a pipeline."""
        if pipeline_id in self._store:
            del self._store[pipeline_id]
