"""Terminal dashboard for pipeline health overview."""
from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.collector import MetricsCollector
from pipewatch.reporter import Reporter, PipelineReport
from pipewatch.metrics import MetricStatus


@dataclass
class DashboardRow:
    pipeline: str
    status: str
    error_rate: float
    avg_duration: float
    record_count: int
    alert_count: int


class Dashboard:
    def __init__(self, reporter: Reporter):
        self.reporter = reporter

    def get_rows(self, pipelines: List[str]) -> List[DashboardRow]:
        rows = []
        for name in pipelines:
            report = self.reporter.report(name)
            metric = report.latest
            rows.append(DashboardRow(
                pipeline=name,
                status=report.status,
                error_rate=metric.error_rate if metric else 0.0,
                avg_duration=metric.duration_seconds if metric else 0.0,
                record_count=metric.record_count if metric else 0,
                alert_count=len(report.alerts),
            ))
        return rows

    def render(self, pipelines: List[str]) -> str:
        rows = self.get_rows(pipelines)
        if not rows:
            return "No pipelines to display.\n"
        header = f"{'Pipeline':<20} {'Status':<10} {'Errors':>8} {'Duration':>10} {'Records':>8} {'Alerts':>7}"
        sep = "-" * len(header)
        lines = [header, sep]
        status_symbols = {
            MetricStatus.OK.value: "✓",
            MetricStatus.WARNING.value: "!",
            MetricStatus.CRITICAL.value: "✗",
            MetricStatus.UNKNOWN.value: "?",
        }
        for row in rows:
            symbol = status_symbols.get(row.status, "?")
            lines.append(
                f"{row.pipeline:<20} {symbol+' '+row.status:<10} {row.error_rate:>8.2%} "
                f"{row.avg_duration:>9.2f}s {row.record_count:>8} {row.alert_count:>7}"
            )
        return "\n".join(lines) + "\n"
