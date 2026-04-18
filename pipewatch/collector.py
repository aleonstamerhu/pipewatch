"""Metric collection and in-memory storage for pipeline metrics."""

from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.metrics import PipelineMetric, MetricStatus


class MetricsCollector:
    """Collects and stores pipeline metrics in memory."""

    def __init__(self, max_history: int = 100):
        self._max_history = max_history
        self._store: Dict[str, List[PipelineMetric]] = {}

    def record(
        self,
        pipeline_name: str,
        rows_processed: int,
        error_count: int,
        duration_seconds: float,
        max_errors: int = 0,
        max_duration_seconds: float = 300.0,
        timestamp: Optional[datetime] = None,
    ) -> PipelineMetric:
        """Record a new metric entry and return the computed metric."""
        metric = PipelineMetric(
            pipeline_name=pipeline_name,
            rows_processed=rows_processed,
            error_count=error_count,
            duration_seconds=duration_seconds,
            timestamp=timestamp or datetime.utcnow(),
        )
        metric.compute_status(max_errors=max_errors, max_duration_seconds=max_duration_seconds)

        history = self._store.setdefault(pipeline_name, [])
        history.append(metric)
        if len(history) > self._max_history:
            history.pop(0)

        return metric

    def latest(self, pipeline_name: str) -> Optional[PipelineMetric]:
        """Return the most recent metric for a pipeline."""
        history = self._store.get(pipeline_name)
        return history[-1] if history else None

    def history(self, pipeline_name: str) -> List[PipelineMetric]:
        """Return full history for a pipeline."""
        return list(self._store.get(pipeline_name, []))

    def all_pipelines(self) -> List[str]:
        return list(self._store.keys())

    def summary(self) -> Dict[str, str]:
        """Return latest status for all tracked pipelines."""
        return {
            name: (self.latest(name).status.value if self.latest(name) else MetricStatus.UNKNOWN.value)
            for name in self.all_pipelines()
        }
