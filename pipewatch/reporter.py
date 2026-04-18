"""Reporting module for summarizing pipeline health metrics."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewatch.alerts import Alert, AlertEngine
from pipewatch.collector import MetricsCollector
from pipewatch.metrics import MetricStatus, PipelineMetric


@dataclass
class PipelineReport:
    pipeline_name: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    latest_metric: Optional[PipelineMetric] = None
    alerts: List[Alert] = field(default_factory=list)
    history_count: int = 0

    @property
    def status(self) -> MetricStatus:
        if self.latest_metric is None:
            return MetricStatus.UNKNOWN
        return self.latest_metric.status

    def summary(self) -> str:
        lines = [
            f"Pipeline : {self.pipeline_name}",
            f"Status   : {self.status.value.upper()}",
            f"Snapshots: {self.history_count}",
        ]
        if self.latest_metric:
            m = self.latest_metric
            lines.append(f"Last run : duration={m.duration_seconds}s  errors={m.error_count}  rows={m.rows_processed}")
        if self.alerts:
            lines.append(f"Alerts ({len(self.alerts)}):")
            for alert in self.alerts:
                lines.append(f"  - {alert}")
        else:
            lines.append("Alerts   : none")
        return "\n".join(lines)


class Reporter:
    def __init__(self, collector: MetricsCollector, alert_engine: AlertEngine) -> None:
        self.collector = collector
        self.alert_engine = alert_engine

    def report(self, pipeline_name: str) -> PipelineReport:
        latest = self.collector.latest(pipeline_name)
        hist = self.collector.history(pipeline_name)
        alerts = self.alert_engine.evaluate(latest) if latest else []
        return PipelineReport(
            pipeline_name=pipeline_name,
            latest_metric=latest,
            alerts=alerts,
            history_count=len(hist),
        )

    def report_all(self) -> List[PipelineReport]:
        return [self.report(name) for name in self.collector.pipelines()]
