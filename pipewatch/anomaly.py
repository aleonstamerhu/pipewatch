"""Anomaly detection for pipeline metrics using simple statistical methods."""

from dataclasses import dataclass
from typing import List, Optional
from pipewatch.metrics import PipelineMetric


@dataclass
class AnomalyResult:
    pipeline: str
    field: str
    value: float
    mean: float
    std: float
    z_score: float
    is_anomaly: bool

    def summary(self) -> str:
        flag = "ANOMALY" if self.is_anomaly else "ok"
        return (
            f"[{flag}] {self.pipeline}.{self.field}: value={self.value:.2f} "
            f"mean={self.mean:.2f} std={self.std:.2f} z={self.z_score:.2f}"
        )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def detect_anomaly(
    pipeline: str,
    field: str,
    history: List[float],
    current: float,
    threshold: float = 2.5,
) -> Optional[AnomalyResult]:
    """Detect if current value is anomalous compared to history."""
    if len(history) < 3:
        return None
    mean = _mean(history)
    std = _std(history, mean)
    if std == 0:
        return None
    z = abs(current - mean) / std
    return AnomalyResult(
        pipeline=pipeline,
        field=field,
        value=current,
        mean=mean,
        std=std,
        z_score=z,
        is_anomaly=z >= threshold,
    )


def analyze_metrics(
    pipeline: str,
    history: List[PipelineMetric],
    threshold: float = 2.5,
) -> List[AnomalyResult]:
    """Analyze error_count and duration_seconds for anomalies."""
    if len(history) < 4:
        return []
    results = []
    for field in ("error_count", "duration_seconds"):
        values = [getattr(m, field) for m in history]
        past, current = values[:-1], values[-1]
        result = detect_anomaly(pipeline, field, past, current, threshold)
        if result is not None:
            results.append(result)
    return results
