"""Tests for pipewatch/grouping.py"""

import pytest
from unittest.mock import MagicMock
from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.tagging import TagStore
from pipewatch.collector import MetricsCollector
from pipewatch.grouping import GroupSummary, group_by_tag, group_all


def make_metric(name: str, status: MetricStatus) -> PipelineMetric:
    m = MagicMock(spec=PipelineMetric)
    m.pipeline = name
    m.status = status
    return m


@pytest.fixture
def store():
    s = TagStore()
    s.add("pipeline_a", "team-alpha")
    s.add("pipeline_b", "team-alpha")
    s.add("pipeline_c", "team-beta")
    return s


@pytest.fixture
def collector(store):
    c = MagicMock(spec=MetricsCollector)
    data = {
        "pipeline_a": make_metric("pipeline_a", MetricStatus.OK),
        "pipeline_b": make_metric("pipeline_b", MetricStatus.CRITICAL),
        "pipeline_c": make_metric("pipeline_c", MetricStatus.WARNING),
    }
    c.latest.side_effect = lambda name: data.get(name)
    return c


def test_group_by_tag_returns_correct_pipelines(store, collector):
    result = group_by_tag("team-alpha", store, collector)
    assert result is not None
    assert set(result.pipelines) == {"pipeline_a", "pipeline_b"}


def test_group_by_tag_counts_statuses(store, collector):
    result = group_by_tag("team-alpha", store, collector)
    assert result.ok_count == 1
    assert result.critical_count == 1
    assert result.warning_count == 0
    assert result.unknown_count == 0


def test_dominant_status_critical_wins(store, collector):
    result = group_by_tag("team-alpha", store, collector)
    assert result.dominant_status() == MetricStatus.CRITICAL


def test_dominant_status_warning_when_no_critical(store, collector):
    result = group_by_tag("team-beta", store, collector)
    assert result.dominant_status() == MetricStatus.WARNING


def test_group_by_tag_returns_none_for_unknown_tag(store, collector):
    result = group_by_tag("nonexistent", store, collector)
    assert result is None


def test_group_by_tag_unknown_when_no_metric(store):
    c = MagicMock(spec=MetricsCollector)
    c.latest.return_value = None
    result = group_by_tag("team-alpha", store, c)
    assert result is not None
    assert result.unknown_count == 2
    assert result.dominant_status() == MetricStatus.UNKNOWN


def test_group_all_returns_all_tags(store, collector):
    results = group_all(store, collector)
    tags = {r.tag for r in results}
    assert "team-alpha" in tags
    assert "team-beta" in tags


def test_summary_string_contains_tag(store, collector):
    result = group_by_tag("team-alpha", store, collector)
    assert "team-alpha" in result.summary()
    assert "CRITICAL" in result.summary()
