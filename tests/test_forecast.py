"""Tests for pipewatch.forecast."""

from unittest.mock import MagicMock

import pytest

from pipewatch.forecast import ForecastResult, forecast_all, forecast_pipeline
from pipewatch.metrics import MetricStatus, PipelineMetric


def make_metric(pipeline: str, error_count: int = 0, duration: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        error_count=error_count,
        duration_seconds=duration,
        rows_processed=100,
        status=MetricStatus.OK,
    )


def test_forecast_too_few_samples_returns_none():
    metrics = [make_metric("p", error_count=i) for i in range(2)]
    result = forecast_pipeline("p", metrics, metric="error_count", min_samples=3)
    assert result is None


def test_forecast_single_sample_at_min_returns_result():
    metrics = [make_metric("p", error_count=5)] * 3
    result = forecast_pipeline("p", metrics, metric="error_count", min_samples=3)
    assert result is not None
    assert result.forecasted_value == pytest.approx(5.0, abs=0.01)
    assert result.slope == pytest.approx(0.0, abs=0.01)


def test_forecast_rising_trend():
    # error counts: 0, 1, 2, 3, 4 — slope should be 1.0
    metrics = [make_metric("p", error_count=i) for i in range(5)]
    result = forecast_pipeline("p", metrics, metric="error_count", horizon=1)
    assert result is not None
    assert result.slope == pytest.approx(1.0, abs=0.01)
    assert result.forecasted_value == pytest.approx(5.0, abs=0.1)


def test_forecast_falling_trend():
    metrics = [make_metric("p", error_count=i) for i in range(10, 5, -1)]
    result = forecast_pipeline("p", metrics, metric="error_count", horizon=1)
    assert result is not None
    assert result.slope < 0


def test_forecast_horizon_affects_value():
    metrics = [make_metric("p", error_count=i) for i in range(5)]
    r1 = forecast_pipeline("p", metrics, metric="error_count", horizon=1)
    r2 = forecast_pipeline("p", metrics, metric="error_count", horizon=3)
    assert r2.forecasted_value > r1.forecasted_value


def test_forecast_duration_field():
    metrics = [make_metric("p", duration=float(i)) for i in range(1, 6)]
    result = forecast_pipeline("p", metrics, metric="duration_seconds", horizon=1)
    assert result is not None
    assert result.metric == "duration_seconds"
    assert result.forecasted_value == pytest.approx(6.0, abs=0.1)


def test_summary_contains_pipeline_name():
    result = ForecastResult(
        pipeline="etl_main",
        metric="error_count",
        samples=5,
        forecasted_value=3.5,
        horizon=1,
        slope=0.5,
    )
    assert "etl_main" in result.summary()
    assert "rising" in result.summary()


def test_forecast_all_skips_pipelines_with_too_few_samples():
    collector = MagicMock()
    collector.pipelines.return_value = ["p1", "p2"]
    collector.history.side_effect = lambda name: (
        [make_metric(name, error_count=i) for i in range(5)] if name == "p1" else [make_metric(name)]
    )
    results = forecast_all(collector, metric="error_count", min_samples=3)
    assert len(results) == 1
    assert results[0].pipeline == "p1"


def test_forecast_all_empty_collector():
    collector = MagicMock()
    collector.pipelines.return_value = []
    results = forecast_all(collector)
    assert results == []
