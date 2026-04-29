"""Filtering module for querying pipeline metrics by various criteria."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class FilterCriteria:
    statuses: Optional[List[MetricStatus]] = None
    min_error_rate: Optional[float] = None
    max_error_rate: Optional[float] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    name_contains: Optional[str] = None
    tags: Optional[List[str]] = None


def _matches(metric: PipelineMetric, criteria: FilterCriteria, pipeline_tags: Optional[List[str]] = None) -> bool:
    if criteria.statuses and metric.status not in criteria.statuses:
        return False
    if criteria.min_error_rate is not None and metric.error_rate < criteria.min_error_rate:
        return False
    if criteria.max_error_rate is not None and metric.error_rate > criteria.max_error_rate:
        return False
    if criteria.min_duration is not None and metric.duration_seconds < criteria.min_duration:
        return False
    if criteria.max_duration is not None and metric.duration_seconds > criteria.max_duration:
        return False
    if criteria.name_contains and criteria.name_contains.lower() not in metric.pipeline_name.lower():
        return False
    if criteria.tags:
        tags = pipeline_tags or []
        if not all(t in tags for t in criteria.tags):
            return False
    return True


def filter_metrics(
    metrics: List[PipelineMetric],
    criteria: FilterCriteria,
    tag_map: Optional[dict] = None,
) -> List[PipelineMetric]:
    """Return metrics matching all criteria. tag_map maps pipeline_name -> list of tags."""
    tag_map = tag_map or {}
    return [
        m for m in metrics
        if _matches(m, criteria, tag_map.get(m.pipeline_name))
    ]


def filter_summary(metrics: List[PipelineMetric]) -> dict:
    """Return a count breakdown by status for a filtered list."""
    counts: dict = {s.value: 0 for s in MetricStatus}
    for m in metrics:
        counts[m.status.value] += 1
    counts["total"] = len(metrics)
    return counts
