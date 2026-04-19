"""Tests for pipewatch.trend module."""
import pytest
from pipewatch.metrics import MetricStatus
from pipewatch.trend import analyze_trend, analyze_all, TrendResult
from pipewatch.collector import MetricsCollector
from pipewatch.metrics import PipelineMetric
from datetime import datetime


def make_metric(pipeline="pipe", duration=1.0, errors=0, records=100, status=MetricStatus.OK):
    return PipelineMetric(
        pipeline_name=pipeline,
        duration_seconds=duration,
        record_count=records,
        error_count=errors,
        timestamp=datetime.utcnow(),
        status=status,
    )


def test_analyze_trend_empty_returns_none():
    assert analyze_trend("pipe", []) is None


def test_analyze_trend_single_sample():
    result = analyze_trend("pipe", [make_metric(duration=2.0)])
    assert result is not None
    assert result.sample_count == 1
    assert result.direction == "unknown"
    assert result.avg_duration == pytest.approx(2.0)


def test_analyze_trend_stable():
    metrics = [make_metric(duration=1.0) for _ in range(6)]
    result = analyze_trend("pipe", metrics)
    assert result.direction == "stable"


def test_analyze_trend_degrading():
    metrics = [make_metric(duration=d) for d in [1.0, 1.0, 1.0, 5.0, 5.0, 5.0]]
    result = analyze_trend("pipe", metrics)
    assert result.direction == "degrading"


def test_analyze_trend_improving():
    metrics = [make_metric(duration=d) for d in [5.0, 5.0, 5.0, 1.0, 1.0, 1.0]]
    result = analyze_trend("pipe", metrics)
    assert result.direction == "improving"


def test_analyze_all_empty_collector():
    collector = MetricsCollector()
    results = analyze_all(collector)
    assert results == []


def test_analyze_all_multiple_pipelines():
    collector = MetricsCollector()
    for _ in range(4):
        collector.record("alpha", 1.0, 100, 0)
        collector.record("beta", 2.0, 50, 5)
    results = analyze_all(collector)
    names = {r.pipeline for r in results}
    assert "alpha" in names
    assert "beta" in names


def test_trend_summary_string():
    result = TrendResult(
        pipeline="mypipe",
        sample_count=10,
        avg_duration=3.5,
        avg_error_rate=0.02,
        direction="stable",
        latest_status=MetricStatus.OK,
    )
    summary = result.summary()
    assert "mypipe" in summary
    assert "stable" in summary
