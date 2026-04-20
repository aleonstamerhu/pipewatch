"""Correlation analysis between pipeline metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pipewatch.metrics import PipelineMetric


@dataclass
class CorrelationResult:
    pipeline_a: str
    pipeline_b: str
    coefficient: float  # Pearson r, -1.0 to 1.0
    sample_count: int

    def summary(self) -> str:
        strength = _strength_label(self.coefficient)
        direction = "positive" if self.coefficient >= 0 else "negative"
        return (
            f"{self.pipeline_a} <-> {self.pipeline_b}: "
            f"r={self.coefficient:.3f} ({strength} {direction}, n={self.sample_count})"
        )


def _strength_label(r: float) -> str:
    abs_r = abs(r)
    if abs_r >= 0.8:
        return "strong"
    if abs_r >= 0.5:
        return "moderate"
    if abs_r >= 0.2:
        return "weak"
    return "negligible"


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    std_x = (sum((x - mean_x) ** 2 for x in xs) ** 0.5)
    std_y = (sum((y - mean_y) ** 2 for y in ys) ** 0.5)
    if std_x == 0 or std_y == 0:
        return None
    return cov / (std_x * std_y)


def correlate_pipelines(
    history_a: List[PipelineMetric],
    history_b: List[PipelineMetric],
    pipeline_a: str,
    pipeline_b: str,
) -> Optional[CorrelationResult]:
    """Compute Pearson correlation of error_count between two pipelines."""
    min_len = min(len(history_a), len(history_b))
    if min_len < 2:
        return None
    xs = [float(m.error_count) for m in history_a[-min_len:]]
    ys = [float(m.error_count) for m in history_b[-min_len:]]
    r = _pearson(xs, ys)
    if r is None:
        return None
    return CorrelationResult(
        pipeline_a=pipeline_a,
        pipeline_b=pipeline_b,
        coefficient=round(r, 6),
        sample_count=min_len,
    )


def correlate_all(
    histories: Dict[str, List[PipelineMetric]],
) -> List[CorrelationResult]:
    """Compute pairwise correlations for all pipelines."""
    results: List[CorrelationResult] = []
    names = sorted(histories.keys())
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            result = correlate_pipelines(histories[a], histories[b], a, b)
            if result is not None:
                results.append(result)
    return results
