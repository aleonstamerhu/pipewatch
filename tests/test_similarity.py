"""Tests for pipewatch.similarity module."""

import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.collector import MetricsCollector
from pipewatch.similarity import (
    compute_similarity,
    find_similar_pipelines,
    SimilarityResult,
    _similarity_label,
)


def make_metric(pipeline: str, errors: int, duration: float) -> PipelineMetric:
    return PipelineMetric(
        pipeline_name=pipeline,
        error_count=errors,
        duration_seconds=duration,
        rows_processed=100,
        status=MetricStatus.OK,
    )


@pytest.fixture
def collector():
    c = MetricsCollector()
    for i in range(5):
        c.record(make_metric("pipe_a", errors=i, duration=float(i * 2)))
        c.record(make_metric("pipe_b", errors=i, duration=float(i * 2)))
        c.record(make_metric("pipe_c", errors=4 - i, duration=float((4 - i) * 2)))
    return c


def test_similarity_label_very_similar():
    assert _similarity_label(0.95) == "very similar"


def test_similarity_label_dissimilar():
    assert _similarity_label(0.2) == "dissimilar"


def test_similarity_label_similar():
    assert _similarity_label(0.75) == "similar"


def test_compute_similarity_identical_pipelines(collector):
    result = compute_similarity(collector, "pipe_a", "pipe_b")
    assert result is not None
    assert isinstance(result, SimilarityResult)
    assert result.score == pytest.approx(1.0, abs=0.01)
    assert result.label == "very similar"


def test_compute_similarity_inverse_pipelines(collector):
    result = compute_similarity(collector, "pipe_a", "pipe_c")
    assert result is not None
    # pipe_c is inversely correlated — absolute value should still be high
    assert result.score >= 0.9


def test_compute_similarity_too_few_samples():
    c = MetricsCollector()
    c.record(make_metric("pipe_a", errors=1, duration=1.0))
    c.record(make_metric("pipe_b", errors=1, duration=1.0))
    result = compute_similarity(c, "pipe_a", "pipe_b", min_samples=3)
    assert result is None


def test_compute_similarity_missing_pipeline(collector):
    result = compute_similarity(collector, "pipe_a", "nonexistent")
    assert result is None


def test_find_similar_pipelines_returns_sorted(collector):
    results = find_similar_pipelines(collector, "pipe_a", threshold=0.0)
    assert len(results) == 2
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_find_similar_pipelines_threshold_filters(collector):
    results = find_similar_pipelines(collector, "pipe_a", threshold=0.99)
    assert all(r.score >= 0.99 for r in results)


def test_similarity_summary_format(collector):
    result = compute_similarity(collector, "pipe_a", "pipe_b")
    assert result is not None
    summary = result.summary()
    assert "pipe_a" in summary
    assert "pipe_b" in summary
    assert "similarity=" in summary
