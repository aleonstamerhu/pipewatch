"""Reporter module: generates pipeline reports from collected metrics and alerts."""
from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.collector import MetricsCollector
from pipewatch.alerts import AlertEngine, Alert


@dataclass
class PipelineReport:
    latest: Optional[PipelineMetric]
    alerts: List[Alert]
    history: List[PipelineMetric]

    @property
    def status(self) -> str:
        if self.latest is None:
            return MetricStatus.UNKNOWN.value
        return self.latest.status.value

    @property
    def summary(self) -> str:
        if self.latest is None:
            return "No data available."
        m = self.latest
        return (
            f"records={m.record_count}, "
            f"errors={m.error_rate:.2%}, "
            f"duration={m.duration_seconds:.2f}s"
        )


class Reporter:
    def __init__(self, collector: MetricsCollector, engine: AlertEngine):
        self.collector = collector
        self.engine = engine

    def report(self, pipeline: str) -> PipelineReport:
        latest = self.collector.latest(pipeline)
        history = self.collector.history(pipeline)
        alerts = self.engine.evaluate(latest) if latest else []
        return PipelineReport(latest=latest, alerts=alerts, history=list(history))

    def report_all(self) -> dict:
        pipelines = list(self.collector._latest.keys())
        return {name: self.report(name) for name in pipelines}
