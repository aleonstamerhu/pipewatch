"""Tests for pipewatch.filtering module."""

import pytest
from datetime import datetime, timezone
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.filtering import FilterCriteria, filter_metrics, filter_summary


def make_metric(name, status=MetricStatus.OK, error_rate=0.0, duration=10.0):
    return PipelineMetric(
        pipeline_name=name,
        status=status,
        error_rate=error_rate,
        duration_seconds=duration,
        row_count=100,
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def metrics():
    return [
        make_metric("alpha", MetricStatus.OK, 0.0, 5.0),
        make_metric("beta", MetricStatus.WARNING, 0.05, 30.0),
        make_metric("gamma", MetricStatus.CRITICAL, 0.5, 120.0),
        make_metric("delta", MetricStatus.UNKNOWN, 0.0, 0.0),
    ]


def test_filter_by_status(metrics):
    criteria = FilterCriteria(statuses=[MetricStatus.OK])
    result = filter_metrics(metrics, criteria)
    assert len(result) == 1
    assert result[0].pipeline_name == "alpha"


def test_filter_by_multiple_statuses(metrics):
    criteria = FilterCriteria(statuses=[MetricStatus.OK, MetricStatus.WARNING])
    result = filter_metrics(metrics, criteria)
    assert {m.pipeline_name for m in result} == {"alpha", "beta"}


def test_filter_by_min_error_rate(metrics):
    criteria = FilterCriteria(min_error_rate=0.04)
    result = filter_metrics(metrics, criteria)
    assert {m.pipeline_name for m in result} == {"beta", "gamma"}


def test_filter_by_max_duration(metrics):
    criteria = FilterCriteria(max_duration=30.0)
    result = filter_metrics(metrics, criteria)
    assert {m.pipeline_name for m in result} == {"alpha", "beta", "delta"}


def test_filter_by_name_contains(metrics):
    criteria = FilterCriteria(name_contains="lph")
    result = filter_metrics(metrics, criteria)
    assert len(result) == 1
    assert result[0].pipeline_name == "alpha"


def test_filter_by_tag(metrics):
    tag_map = {"alpha": ["prod"], "beta": ["dev"], "gamma": ["prod"], "delta": []}
    criteria = FilterCriteria(tags=["prod"])
    result = filter_metrics(metrics, criteria, tag_map)
    assert {m.pipeline_name for m in result} == {"alpha", "gamma"}


def test_filter_no_criteria_returns_all(metrics):
    criteria = FilterCriteria()
    result = filter_metrics(metrics, criteria)
    assert len(result) == len(metrics)


def test_filter_summary_counts(metrics):
    counts = filter_summary(metrics)
    assert counts["total"] == 4
    assert counts[MetricStatus.OK.value] == 1
    assert counts[MetricStatus.CRITICAL.value] == 1


def test_filter_combined_criteria(metrics):
    criteria = FilterCriteria(min_duration=10.0, max_error_rate=0.1)
    result = filter_metrics(metrics, criteria)
    assert {m.pipeline_name for m in result} == {"beta"}
