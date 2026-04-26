"""Pipeline ranking module.

Ranks pipelines by overall health using a composite score derived from
health scores, anomaly detection, trend direction, and alert frequency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipewatch.collector import MetricsCollector
from pipewatch.health import score_pipeline, HealthScore
from pipewatch.anomaly import detect_anomaly, AnomalyResult
from pipewatch.trend import analyze_trend, TrendResult
from pipewatch.alerts import AlertEngine


@dataclass
class PipelineRank:
    """Composite ranking entry for a single pipeline."""

    pipeline: str
    rank: int
    composite_score: float  # 0.0 (worst) to 1.0 (best)
    health_score: Optional[HealthScore]
    anomaly: Optional[AnomalyResult]
    trend: Optional[TrendResult]
    alert_count: int

    def summary(self) -> str:
        """Return a human-readable one-line summary of this rank entry."""
        health = f"{self.health_score.score:.2f}" if self.health_score else "N/A"
        trend_dir = self.trend.direction if self.trend else "unknown"
        anomaly_flag = "⚠ anomaly" if (self.anomaly and self.anomaly.is_anomaly) else "ok"
        return (
            f"#{self.rank} {self.pipeline} "
            f"| composite={self.composite_score:.2f} "
            f"| health={health} "
            f"| trend={trend_dir} "
            f"| {anomaly_flag} "
            f"| alerts={self.alert_count}"
        )


# Weights used in composite score calculation
_WEIGHT_HEALTH = 0.50
_WEIGHT_TREND = 0.20
_WEIGHT_ANOMALY = 0.15
_WEIGHT_ALERTS = 0.15

_TREND_SCORE = {
    "improving": 1.0,
    "stable": 0.7,
    "degrading": 0.2,
    "unknown": 0.5,
}


def _compute_composite(
    health: Optional[HealthScore],
    trend: Optional[TrendResult],
    anomaly: Optional[AnomalyResult],
    alert_count: int,
    max_alerts: int,
) -> float:
    """Compute a composite score in [0.0, 1.0] for a pipeline."""
    health_val = health.score if health else 0.5

    direction = trend.direction if trend else "unknown"
    trend_val = _TREND_SCORE.get(direction, 0.5)

    # Anomaly: no anomaly = 1.0, anomaly detected = 0.0
    if anomaly is None:
        anomaly_val = 0.5  # not enough data — neutral
    elif anomaly.is_anomaly:
        anomaly_val = 0.0
    else:
        anomaly_val = 1.0

    # Alert penalty: more alerts → lower score
    if max_alerts > 0:
        alert_val = 1.0 - min(alert_count / max_alerts, 1.0)
    else:
        alert_val = 1.0

    return (
        _WEIGHT_HEALTH * health_val
        + _WEIGHT_TREND * trend_val
        + _WEIGHT_ANOMALY * anomaly_val
        + _WEIGHT_ALERTS * alert_val
    )


def rank_pipelines(
    collector: MetricsCollector,
    alert_engine: Optional[AlertEngine] = None,
) -> list[PipelineRank]:
    """Rank all known pipelines by composite health score.

    Args:
        collector: The metrics collector holding pipeline history.
        alert_engine: Optional alert engine used to count recent alerts per pipeline.

    Returns:
        A list of PipelineRank entries sorted best-to-worst (rank 1 = healthiest).
    """
    pipelines = collector.list_pipelines()
    if not pipelines:
        return []

    entries: list[dict] = []

    # Pre-compute max alert count for normalisation
    alert_counts: dict[str, int] = {}
    if alert_engine is not None:
        for name in pipelines:
            metrics = collector.history(name)
            count = 0
            for m in metrics:
                alerts = alert_engine.evaluate(m)
                count += len(alerts)
            alert_counts[name] = count
    max_alerts = max(alert_counts.values(), default=1) or 1

    for name in pipelines:
        metrics = collector.history(name)
        health = score_pipeline(name, metrics) if metrics else None
        trend = analyze_trend(metrics) if metrics else None
        anomaly = detect_anomaly(metrics) if metrics else None
        a_count = alert_counts.get(name, 0)

        composite = _compute_composite(health, trend, anomaly, a_count, max_alerts)
        entries.append(
            {
                "pipeline": name,
                "composite_score": composite,
                "health_score": health,
                "anomaly": anomaly,
                "trend": trend,
                "alert_count": a_count,
            }
        )

    # Sort descending by composite score
    entries.sort(key=lambda e: e["composite_score"], reverse=True)

    return [
        PipelineRank(
            pipeline=e["pipeline"],
            rank=idx + 1,
            composite_score=round(e["composite_score"], 4),
            health_score=e["health_score"],
            anomaly=e["anomaly"],
            trend=e["trend"],
            alert_count=e["alert_count"],
        )
        for idx, e in enumerate(entries)
    ]
