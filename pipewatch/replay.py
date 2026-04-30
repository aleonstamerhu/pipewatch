"""Replay historical metrics through the alert engine for retrospective analysis."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from pipewatch.metrics import PipelineMetric
from pipewatch.alerts import Alert, AlertEngine
from pipewatch.audit import AuditLog


@dataclass
class ReplayResult:
    pipeline: str
    total_metrics: int
    alerts_fired: List[Alert] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def summary(self) -> str:
        n = len(self.alerts_fired)
        span = ""
        if self.start_time and self.end_time:
            delta = (self.end_time - self.start_time).total_seconds()
            span = f" over {delta:.0f}s"
        return (
            f"[{self.pipeline}] replayed {self.total_metrics} metric(s){span}, "
            f"{n} alert(s) fired"
        )


def replay_pipeline(
    pipeline: str,
    metrics: List[PipelineMetric],
    engine: AlertEngine,
) -> ReplayResult:
    """Run a list of historical metrics through the alert engine."""
    if not metrics:
        return ReplayResult(pipeline=pipeline, total_metrics=0)

    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
    alerts: List[Alert] = []

    for metric in sorted_metrics:
        fired = engine.evaluate(metric)
        alerts.extend(fired)

    return ReplayResult(
        pipeline=pipeline,
        total_metrics=len(sorted_metrics),
        alerts_fired=alerts,
        start_time=sorted_metrics[0].timestamp,
        end_time=sorted_metrics[-1].timestamp,
    )


def replay_from_audit(
    pipeline: str,
    audit_log: AuditLog,
    engine: AlertEngine,
) -> ReplayResult:
    """Replay metrics stored in the audit log for a given pipeline."""
    entries = audit_log.filter(pipeline=pipeline, entry_type="metric")
    metrics: List[PipelineMetric] = []
    for entry in entries:
        m = entry.data.get("metric")
        if isinstance(m, PipelineMetric):
            metrics.append(m)
    return replay_pipeline(pipeline, metrics, engine)
