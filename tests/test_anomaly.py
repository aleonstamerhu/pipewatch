"""Tests for pipewatch.anomaly module."""

import pytest
from pipewatch.anomaly import detect_anomaly, analyze_metrics, AnomalyResult
from pipewatch.metrics import PipelineMetric, MetricStatus


def make_metric(errors=0, duration=1.0):
    return PipelineMetric(
        pipeline="pipe",
        rows_processed=100,
        error_count=errors,
        duration_seconds=duration,
        status=MetricStatus.OK,
    )


def test_detect_anomaly_too_few_samples():
    result = detect_anomaly("p", "errors", [1.0, 2.0], 5.0)
    assert result is None


def test_detect_anomaly_zero_std():
    result = detect_anomaly("p", "errors", [2.0, 2.0, 2.0], 2.0)
    assert result is None


def test_detect_anomaly_normal_value():
    history = [1.0, 1.1, 0.9, 1.05, 0.95]
    result = detect_anomaly("p", "dur", history, 1.0, threshold=2.5)
    assert result is not None
    assert not result.is_anomaly


def test_detect_anomaly_spike():
    history = [1.0, 1.0, 1.0, 1.0, 1.0]
    result = detect_anomaly("p", "dur", history, 100.0, threshold=2.5)
    assert result is not None
    assert result.is_anomaly
    assert result.z_score > 2.5


def test_anomaly_result_summary_flagged():
    r = AnomalyResult("pipe", "errors", 50.0, 2.0, 1.0, 48.0, True)
    assert "ANOMALY" in r.summary()
    assert "pipe" in r.summary()


def test_anomaly_result_summary_ok():
    r = AnomalyResult("pipe", "errors", 2.0, 2.0, 1.0, 0.0, False)
    assert "ok" in r.summary()


def test_analyze_metrics_too_few():
    metrics = [make_metric() for _ in range(3)]
    assert analyze_metrics("pipe", metrics) == []


def test_analyze_metrics_stable():
    metrics = [make_metric(errors=1, duration=1.0) for _ in range(6)]
    results = analyze_metrics("pipe", metrics)
    # std is 0 for all fields, so no results returned
    assert results == []


def test_analyze_metrics_detects_spike():
    normal = [make_metric(errors=1, duration=1.0) for _ in range(5)]
    spike = make_metric(errors=1000, duration=500.0)
    metrics = normal + [spike]
    results = analyze_metrics("pipe", metrics, threshold=2.5)
    anomalous = [r for r in results if r.is_anomaly]
    assert len(anomalous) == 2
    fields = {r.field for r in anomalous}
    assert "error_count" in fields
    assert "duration_seconds" in fields
