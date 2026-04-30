"""Periodic digest summarising pipeline health across all tracked pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.collector import MetricsCollector
from pipewatch.health import HealthScore, score_all
from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus


@dataclass
class DigestEntry:
    pipeline: str
    health_score: float
    status: str
    error_rate: float
    avg_duration: float
    alert_count: int

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "health_score": round(self.health_score, 3),
            "status": self.status,
            "error_rate": round(self.error_rate, 4),
            "avg_duration": round(self.avg_duration, 3),
            "alert_count": self.alert_count,
        }


@dataclass
class Digest:
    generated_at: datetime = field(default_factory=datetime.utcnow)
    entries: List[DigestEntry] = field(default_factory=list)
    total_pipelines: int = 0
    healthy_count: int = 0
    degraded_count: int = 0
    critical_count: int = 0

    def summary(self) -> str:
        return (
            f"Digest [{self.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC] "
            f"| Pipelines: {self.total_pipelines} "
            f"| Healthy: {self.healthy_count} "
            f"| Degraded: {self.degraded_count} "
            f"| Critical: {self.critical_count}"
        )


def build_digest(
    collector: MetricsCollector,
    alerts: Optional[List[Alert]] = None,
) -> Digest:
    """Build a Digest from the current collector state and optional alert list."""
    alerts = alerts or []
    scores: Dict[str, HealthScore] = score_all(collector)

    alert_counts: Dict[str, int] = {}
    for alert in alerts:
        alert_counts[alert.pipeline] = alert_counts.get(alert.pipeline, 0) + 1

    entries: List[DigestEntry] = []
    healthy = degraded = critical = 0

    for pipeline, score in scores.items():
        metric = collector.latest(pipeline)
        error_rate = metric.error_rate if metric else 0.0
        avg_duration = metric.duration_seconds if metric else 0.0
        status = metric.status.value if metric else MetricStatus.UNKNOWN.value

        if score.score >= 0.8:
            healthy += 1
        elif score.score >= 0.4:
            degraded += 1
        else:
            critical += 1

        entries.append(
            DigestEntry(
                pipeline=pipeline,
                health_score=score.score,
                status=status,
                error_rate=error_rate,
                avg_duration=avg_duration,
                alert_count=alert_counts.get(pipeline, 0),
            )
        )

    entries.sort(key=lambda e: e.health_score)

    return Digest(
        entries=entries,
        total_pipelines=len(entries),
        healthy_count=healthy,
        degraded_count=degraded,
        critical_count=critical,
    )
