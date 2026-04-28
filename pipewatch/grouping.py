"""Pipeline grouping: group pipelines by tag and compute per-group health summaries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.tagging import TagStore
from pipewatch.collector import MetricsCollector
from pipewatch.metrics import MetricStatus, PipelineMetric


@dataclass
class GroupSummary:
    tag: str
    pipelines: List[str]
    ok_count: int
    warning_count: int
    critical_count: int
    unknown_count: int

    def dominant_status(self) -> MetricStatus:
        if self.critical_count > 0:
            return MetricStatus.CRITICAL
        if self.warning_count > 0:
            return MetricStatus.WARNING
        if self.ok_count > 0:
            return MetricStatus.OK
        return MetricStatus.UNKNOWN

    def summary(self) -> str:
        status = self.dominant_status().value.upper()
        total = len(self.pipelines)
        return (
            f"[{self.tag}] {status} — "
            f"{total} pipeline(s): "
            f"{self.ok_count} ok, {self.warning_count} warning, "
            f"{self.critical_count} critical, {self.unknown_count} unknown"
        )


def group_by_tag(
    tag: str,
    tag_store: TagStore,
    collector: MetricsCollector,
) -> Optional[GroupSummary]:
    """Return a GroupSummary for all pipelines with the given tag."""
    pipelines = tag_store.pipelines_with_tag(tag)
    if not pipelines:
        return None

    counts: Dict[MetricStatus, int] = {
        MetricStatus.OK: 0,
        MetricStatus.WARNING: 0,
        MetricStatus.CRITICAL: 0,
        MetricStatus.UNKNOWN: 0,
    }

    for name in pipelines:
        metric: Optional[PipelineMetric] = collector.latest(name)
        status = metric.status if metric else MetricStatus.UNKNOWN
        counts[status] = counts.get(status, 0) + 1

    return GroupSummary(
        tag=tag,
        pipelines=sorted(pipelines),
        ok_count=counts[MetricStatus.OK],
        warning_count=counts[MetricStatus.WARNING],
        critical_count=counts[MetricStatus.CRITICAL],
        unknown_count=counts[MetricStatus.UNKNOWN],
    )


def group_all(
    tag_store: TagStore,
    collector: MetricsCollector,
) -> List[GroupSummary]:
    """Return GroupSummary for every tag in the store."""
    all_tags = tag_store.all_tags() if hasattr(tag_store, "all_tags") else set(
        t for name in tag_store._data for t in tag_store.get(name)
    )
    results = []
    for tag in sorted(all_tags):
        summary = group_by_tag(tag, tag_store, collector)
        if summary is not None:
            results.append(summary)
    return results
