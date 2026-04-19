"""Trend analysis for pipeline metrics over time."""
from dataclasses import dataclass
from typing import List, Optional
from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class TrendResult:
    pipeline: str
    sample_count: int
    avg_duration: float
    avg_error_rate: float
    direction: str  # 'improving', 'degrading', 'stable', 'unknown'
    latest_status: MetricStatus

    def summary(self) -> str:
        return (
            f"{self.pipeline}: {self.direction} "
            f"(avg_duration={self.avg_duration:.2f}s, "
            f"avg_errors={self.avg_error_rate:.2f}, "
            f"samples={self.sample_count})"
        )


def _direction(values: List[float]) -> str:
    if len(values) < 2:
        return "unknown"
    first_half = values[: len(values) // 2]
    second_half = values[len(values) // 2 :]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    delta = avg_second - avg_first
    if abs(delta) < 0.05 * (avg_first + 1e-9):
        return "stable"
    return "degrading" if delta > 0 else "improving"


def analyze_trend(pipeline: str, history: List[PipelineMetric]) -> Optional[TrendResult]:
    if not history:
        return None
    durations = [m.duration_seconds for m in history]
    error_rates = [m.error_count / max(m.record_count, 1) for m in history]
    direction = _direction(durations)
    return TrendResult(
        pipeline=pipeline,
        sample_count=len(history),
        avg_duration=sum(durations) / len(durations),
        avg_error_rate=sum(error_rates) / len(error_rates),
        direction=direction,
        latest_status=history[-1].status,
    )


def analyze_all(collector) -> List[TrendResult]:
    results = []
    for name in collector.pipelines():
        hist = collector.history(name)
        result = analyze_trend(name, hist)
        if result:
            results.append(result)
    return results
