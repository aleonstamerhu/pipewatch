"""Tests for pipewatch.aggregation."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.aggregation import (
    aggregate_pipeline,
    aggregate_all,
    AggregationResult,
    _dominant_status,
)


def make_metric(
    name: str = "pipe",
    duration: float = 1.0,
    error_rate: float = 0.0,
    status: MetricStatus = MetricStatus.OK,
) -> PipelineMetric:
    m = MagicMock(spec=PipelineMetric)
    m.pipeline_name = name
    m.duration_seconds = duration
    m.error_rate = error_rate
    m.status = status
    return m


def test_aggregate_empty_returns_none():
    assert aggregate_pipeline([]) is None


def test_aggregate_single_metric():
    m = make_metric(duration=5.0, error_rate=0.1)
    result = aggregate_pipeline([m])
    assert isinstance(result, AggregationResult)
    assert result.sample_count == 1
    assert result.avg_duration == pytest.approx(5.0)
    assert result.min_duration == pytest.approx(5.0)
    assert result.max_duration == pytest.approx(5.0)
    assert result.avg_error_rate == pytest.approx(0.1)


def test_aggregate_multiple_metrics():
    metrics = [
        make_metric(duration=2.0, error_rate=0.0),
        make_metric(duration=4.0, error_rate=0.2),
        make_metric(duration=6.0, error_rate=0.1),
    ]
    result = aggregate_pipeline(metrics)
    assert result.sample_count == 3
    assert result.avg_duration == pytest.approx(4.0)
    assert result.min_duration == pytest.approx(2.0)
    assert result.max_duration == pytest.approx(6.0)
    assert result.avg_error_rate == pytest.approx(0.1)
    assert result.max_error_rate == pytest.approx(0.2)


def test_dominant_status_critical_wins():
    metrics = [
        make_metric(status=MetricStatus.OK),
        make_metric(status=MetricStatus.CRITICAL),
        make_metric(status=MetricStatus.WARNING),
    ]
    assert _dominant_status(metrics) == MetricStatus.CRITICAL


def test_dominant_status_warning_over_ok():
    metrics = [
        make_metric(status=MetricStatus.OK),
        make_metric(status=MetricStatus.WARNING),
    ]
    assert _dominant_status(metrics) == MetricStatus.WARNING


def test_dominant_status_all_ok():
    metrics = [make_metric(status=MetricStatus.OK) for _ in range(3)]
    assert _dominant_status(metrics) == MetricStatus.OK


def test_aggregate_all_returns_results_per_pipeline():
    collector = MagicMock()
    collector.pipelines.return_value = ["alpha", "beta"]
    collector.history.side_effect = lambda name: [
        make_metric(name=name, duration=1.0, error_rate=0.0)
    ]
    results = aggregate_all(collector)
    assert set(results.keys()) == {"alpha", "beta"}
    assert results["alpha"].pipeline == "alpha"
    assert results["beta"].pipeline == "beta"


def test_aggregate_all_skips_empty_pipelines():
    collector = MagicMock()
    collector.pipelines.return_value = ["empty", "full"]
    collector.history.side_effect = lambda name: [] if name == "empty" else [make_metric(name=name)]
    results = aggregate_all(collector)
    assert "empty" not in results
    assert "full" in results


def test_summary_string_contains_pipeline_name():
    m = make_metric(duration=3.0, error_rate=0.05)
    result = aggregate_pipeline([m])
    assert "pipe" in result.summary()
    assert "samples=1" in result.summary()
