"""Simple linear forecast for pipeline metrics based on recent history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import PipelineMetric


@dataclass
class ForecastResult:
    pipeline: str
    metric: str  # 'error_count' or 'duration_seconds'
    samples: int
    forecasted_value: float
    horizon: int  # steps ahead
    slope: float

    def summary(self) -> str:
        direction = "rising" if self.slope > 0 else ("falling" if self.slope < 0 else "flat")
        return (
            f"{self.pipeline}/{self.metric}: forecasted {self.forecasted_value:.2f} "
            f"in {self.horizon} step(s) [{direction}, slope={self.slope:.4f}]"
        )


def _linear_forecast(values: List[float], horizon: int) -> tuple[float, float]:
    """Return (forecasted_value, slope) using ordinary least squares."""
    n = len(values)
    if n < 2:
        return values[-1], 0.0

    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n

    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    den = sum((x - x_mean) ** 2 for x in xs)

    slope = num / den if den != 0 else 0.0
    intercept = y_mean - slope * x_mean
    forecasted = slope * (n - 1 + horizon) + intercept
    return forecasted, slope


def forecast_pipeline(
    pipeline: str,
    metrics: List[PipelineMetric],
    metric: str = "error_count",
    horizon: int = 1,
    min_samples: int = 3,
) -> Optional[ForecastResult]:
    """Forecast the next value for a given metric field."""
    if len(metrics) < min_samples:
        return None

    values = [float(getattr(m, metric, 0) or 0) for m in metrics]
    forecasted, slope = _linear_forecast(values, horizon)

    return ForecastResult(
        pipeline=pipeline,
        metric=metric,
        samples=len(values),
        forecasted_value=round(forecasted, 4),
        horizon=horizon,
        slope=round(slope, 4),
    )


def forecast_all(
    collector,
    metric: str = "error_count",
    horizon: int = 1,
    min_samples: int = 3,
) -> List[ForecastResult]:
    """Run forecast for every known pipeline in the collector."""
    results = []
    for pipeline in collector.pipelines():
        history = collector.history(pipeline)
        result = forecast_pipeline(pipeline, history, metric=metric, horizon=horizon, min_samples=min_samples)
        if result is not None:
            results.append(result)
    return results
