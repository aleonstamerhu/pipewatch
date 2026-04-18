"""Tests for MetricsCollector."""

import pytest

from pipewatch.collector import MetricsCollector
from pipewatch.metrics import MetricStatus


@pytest.fixture
def collector():
    return MetricsCollector(max_history=5)


def test_record_returns_metric(collector):
    m = collector.record("pipe_a", rows_processed=500, error_count=0, duration_seconds=30.0)
    assert m.pipeline_name == "pipe_a"
    assert m.status != MetricStatus.UNKNOWN


def test_latest_returns_most_recent(collector):
    collector.record("pipe_a", 100, 0, 10.0)
    collector.record("pipe_a", 200, 0, 20.0)
    latest = collector.latest("pipe_a")
    assert latest.rows_processed == 200


def test_latest_unknown_pipeline_returns_none(collector):
    assert collector.latest("nonexistent") is None


def test_history_length_capped(collector):
    for i in range(10):
        collector.record("pipe_b", i * 10, 0, float(i))
    assert len(collector.history("pipe_b")) == 5


def test_all_pipelines(collector):
    collector.record("alpha", 1, 0, 1.0)
    collector.record("beta", 1, 0, 1.0)
    assert set(collector.all_pipelines()) == {"alpha", "beta"}


def test_summary_reflects_latest_status(collector):
    collector.record("pipe_c", 100, 0, 50.0, max_errors=0, max_duration_seconds=300.0)
    summary = collector.summary()
    assert summary["pipe_c"] == MetricStatus.OK.value
