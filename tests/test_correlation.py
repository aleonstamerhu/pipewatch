"""Tests for pipewatch.correlation."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.correlation import (
    correlate_pipelines,
    correlate_all,
    CorrelationResult,
    _pearson,
    _strength_label,
)


def make_metric(pipeline: str, error_count: int = 0, duration: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        pipeline_name=pipeline,
        error_count=error_count,
        duration_seconds=duration,
        rows_processed=100,
        status=MetricStatus.OK,
    )


def test_pearson_perfect_positive():
    r = _pearson([1.0, 2.0, 3.0], [2.0, 4.0, 6.0])
    assert r is not None
    assert abs(r - 1.0) < 1e-9


def test_pearson_perfect_negative():
    r = _pearson([1.0, 2.0, 3.0], [6.0, 4.0, 2.0])
    assert r is not None
    assert abs(r + 1.0) < 1e-9


def test_pearson_zero_std_returns_none():
    r = _pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])
    assert r is None


def test_pearson_too_few_samples():
    assert _pearson([1.0], [1.0]) is None


def test_strength_label():
    assert _strength_label(0.9) == "strong"
    assert _strength_label(0.6) == "moderate"
    assert _strength_label(0.3) == "weak"
    assert _strength_label(0.1) == "negligible"


def test_correlate_pipelines_returns_result():
    hist_a = [make_metric("a", error_count=i) for i in range(5)]
    hist_b = [make_metric("b", error_count=i) for i in range(5)]
    result = correlate_pipelines(hist_a, hist_b, "a", "b")
    assert result is not None
    assert isinstance(result, CorrelationResult)
    assert result.pipeline_a == "a"
    assert result.pipeline_b == "b"
    assert result.sample_count == 5
    assert abs(result.coefficient - 1.0) < 1e-6


def test_correlate_pipelines_too_few_samples():
    hist_a = [make_metric("a", error_count=1)]
    hist_b = [make_metric("b", error_count=2)]
    assert correlate_pipelines(hist_a, hist_b, "a", "b") is None


def test_correlate_pipelines_empty():
    assert correlate_pipelines([], [], "a", "b") is None


def test_correlate_all_returns_pairs():
    histories = {
        "a": [make_metric("a", error_count=i) for i in range(4)],
        "b": [make_metric("b", error_count=i) for i in range(4)],
        "c": [make_metric("c", error_count=3 - i) for i in range(4)],
    }
    results = correlate_all(histories)
    assert len(results) == 3
    pairs = {(r.pipeline_a, r.pipeline_b) for r in results}
    assert ("a", "b") in pairs
    assert ("a", "c") in pairs
    assert ("b", "c") in pairs


def test_correlate_all_single_pipeline():
    histories = {"a": [make_metric("a", error_count=i) for i in range(4)]}
    assert correlate_all(histories) == []


def test_summary_contains_pipeline_names():
    result = CorrelationResult("pipe_a", "pipe_b", 0.75, 10)
    s = result.summary()
    assert "pipe_a" in s
    assert "pipe_b" in s
    assert "0.750" in s
