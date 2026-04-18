"""Pipeline health scoring and aggregation."""
from dataclasses import dataclass, field
from typing import List, Dict
from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class HealthScore:
    pipeline: str
    score: float  # 0.0 (worst) to 1.0 (best)
    status: MetricStatus
    total: int
    ok: int
    warning: int
    critical: int

    def summary(self) -> str:
        return (
            f"{self.pipeline}: score={self.score:.2f} "
            f"[ok={self.ok}, warn={self.warning}, crit={self.critical}]"
        )


def _status_weight(status: MetricStatus) -> float:
    return {
        MetricStatus.OK: 1.0,
        MetricStatus.WARNING: 0.5,
        MetricStatus.CRITICAL: 0.0,
        MetricStatus.UNKNOWN: 0.5,
    }.get(status, 0.5)


def score_pipeline(metrics: List[PipelineMetric]) -> HealthScore:
    if not metrics:
        raise ValueError("Cannot score pipeline with no metrics")

    pipeline = metrics[0].pipeline_name
    counts: Dict[MetricStatus, int] = {s: 0 for s in MetricStatus}
    for m in metrics:
        counts[m.status] = counts.get(m.status, 0) + 1

    total = len(metrics)
    raw_score = sum(_status_weight(m.status) for m in metrics) / total

    if counts[MetricStatus.CRITICAL] > 0:
        overall = MetricStatus.CRITICAL
    elif counts[MetricStatus.WARNING] > 0:
        overall = MetricStatus.WARNING
    elif counts[MetricStatus.UNKNOWN] == total:
        overall = MetricStatus.UNKNOWN
    else:
        overall = MetricStatus.OK

    return HealthScore(
        pipeline=pipeline,
        score=round(raw_score, 4),
        status=overall,
        total=total,
        ok=counts[MetricStatus.OK],
        warning=counts[MetricStatus.WARNING],
        critical=counts[MetricStatus.CRITICAL],
    )


def score_all(metrics_by_pipeline: Dict[str, List[PipelineMetric]]) -> List[HealthScore]:
    return [score_pipeline(v) for v in metrics_by_pipeline.values() if v]
