"""Tests for pipewatch.health module."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.health import HealthScore, score_pipeline, score_all
import datetime


def make_metric(pipeline: str, status: MetricStatus) -> PipelineMetric:
    return PipelineMetric(
        pipeline_name=pipeline,
        timestamp=datetime.datetime.utcnow(),
        duration_seconds=1.0,
        rows_processed=100,
        error_count=0,
        status=status,
    )


def test_score_all_ok():
    metrics = [make_metric("etl", MetricStatus.OK)] * 3
    result = score_pipeline(metrics)
    assert result.score == 1.0
    assert result.status == MetricStatus.OK
    assert result.ok == 3
    assert result.critical == 0


def test_score_all_critical():
    metrics = [make_metric("etl", MetricStatus.CRITICAL)] * 2
    result = score_pipeline(metrics)
    assert result.score == 0.0
    assert result.status == MetricStatus.CRITICAL
    assert result.critical == 2


def test_score_mixed():
    metrics = [
        make_metric("etl", MetricStatus.OK),
        make_metric("etl", MetricStatus.WARNING),
        make_metric("etl", MetricStatus.CRITICAL),
    ]
    result = score_pipeline(metrics)
    assert result.status == MetricStatus.CRITICAL
    assert result.score == pytest.approx((1.0 + 0.5 + 0.0) / 3, rel=1e-3)
    assert result.ok == 1
    assert result.warning == 1
    assert result.critical == 1


def test_score_all_unknown():
    metrics = [make_metric("etl", MetricStatus.UNKNOWN)] * 2
    result = score_pipeline(metrics)
    assert result.status == MetricStatus.UNKNOWN


def test_empty_metrics_raises():
    with pytest.raises(ValueError):
        score_pipeline([])


def test_summary_string():
    metrics = [make_metric("etl", MetricStatus.OK)]
    result = score_pipeline(metrics)
    s = result.summary()
    assert "etl" in s
    assert "score=" in s


def test_score_all_multiple_pipelines():
    data = {
        "a": [make_metric("a", MetricStatus.OK)],
        "b": [make_metric("b", MetricStatus.CRITICAL)],
    }
    results = score_all(data)
    assert len(results) == 2
    pipelines = {r.pipeline for r in results}
    assert pipelines == {"a", "b"}
