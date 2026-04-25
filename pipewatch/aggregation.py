"""Metric aggregation utilities for summarising pipeline history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class AggregationResult:
    pipeline: str
    sample_count: int
    avg_duration: Optional[float]
    max_duration: Optional[float]
    min_duration: Optional[float]
    avg_error_rate: Optional[float]
    max_error_rate: Optional[float]
    dominant_status: MetricStatus

    def summary(self) -> str:
        return (
            f"{self.pipeline}: samples={self.sample_count} "
            f"avg_dur={self.avg_duration:.2f}s "
            f"avg_err={self.avg_error_rate:.4f} "
            f"status={self.dominant_status.value}"
        )


def _dominant_status(metrics: List[PipelineMetric]) -> MetricStatus:
    """Return the most severe status seen across all metrics."""
    order = [MetricStatus.CRITICAL, MetricStatus.WARNING, MetricStatus.OK, MetricStatus.UNKNOWN]
    statuses = {m.status for m in metrics}
    for s in order:
        if s in statuses:
            return s
    return MetricStatus.UNKNOWN


def aggregate_pipeline(metrics: List[PipelineMetric]) -> Optional[AggregationResult]:
    """Compute aggregate statistics for a list of metrics from one pipeline."""
    if not metrics:
        return None

    pipeline = metrics[0].pipeline_name
    durations = [m.duration_seconds for m in metrics if m.duration_seconds is not None]
    errors = [m.error_rate for m in metrics if m.error_rate is not None]

    return AggregationResult(
        pipeline=pipeline,
        sample_count=len(metrics),
        avg_duration=sum(durations) / len(durations) if durations else None,
        max_duration=max(durations) if durations else None,
        min_duration=min(durations) if durations else None,
        avg_error_rate=sum(errors) / len(errors) if errors else None,
        max_error_rate=max(errors) if errors else None,
        dominant_status=_dominant_status(metrics),
    )


def aggregate_all(collector) -> dict[str, AggregationResult]:
    """Aggregate metrics for every known pipeline in the collector."""
    results: dict[str, AggregationResult] = {}
    for name in collector.pipelines():
        history = collector.history(name)
        result = aggregate_pipeline(history)
        if result is not None:
            results[name] = result
    return results
