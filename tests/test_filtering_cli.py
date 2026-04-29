"""Tests for pipewatch.filtering_cli module."""

import pytest
from datetime import datetime, timezone
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.filtering_cli import filtering


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
def runner():
    return CliRunner()


def _mock_collector(pipelines, metrics_map):
    collector = MagicMock()
    collector.pipelines.return_value = pipelines
    collector.latest.side_effect = lambda name: metrics_map.get(name)
    return collector


def test_query_no_pipelines(runner):
    collector = _mock_collector([], {})
    tag_store = MagicMock()
    tag_store.get.return_value = set()
    with patch("pipewatch.filtering_cli._get_collector", return_value=collector), \
         patch("pipewatch.filtering_cli._get_tag_store", return_value=tag_store):
        result = runner.invoke(filtering, ["query"])
    assert result.exit_code == 0
    assert "No pipelines" in result.output


def test_query_returns_matching_pipeline(runner):
    m = make_metric("pipeline_a", MetricStatus.CRITICAL, 0.5, 90.0)
    collector = _mock_collector(["pipeline_a"], {"pipeline_a": m})
    tag_store = MagicMock()
    tag_store.get.return_value = set()
    with patch("pipewatch.filtering_cli._get_collector", return_value=collector), \
         patch("pipewatch.filtering_cli._get_tag_store", return_value=tag_store):
        result = runner.invoke(filtering, ["query", "--status", "critical"])
    assert result.exit_code == 0
    assert "pipeline_a" in result.output
    assert "Matched 1" in result.output


def test_query_invalid_status_exits(runner):
    collector = _mock_collector([], {})
    tag_store = MagicMock()
    with patch("pipewatch.filtering_cli._get_collector", return_value=collector), \
         patch("pipewatch.filtering_cli._get_tag_store", return_value=tag_store):
        result = runner.invoke(filtering, ["query", "--status", "badstatus"])
    assert result.exit_code != 0


def test_query_filters_by_name_contains(runner):
    m1 = make_metric("sales_etl", MetricStatus.OK)
    m2 = make_metric("inventory_etl", MetricStatus.OK)
    collector = _mock_collector(["sales_etl", "inventory_etl"], {"sales_etl": m1, "inventory_etl": m2})
    tag_store = MagicMock()
    tag_store.get.return_value = set()
    with patch("pipewatch.filtering_cli._get_collector", return_value=collector), \
         patch("pipewatch.filtering_cli._get_tag_store", return_value=tag_store):
        result = runner.invoke(filtering, ["query", "--name-contains", "sales"])
    assert result.exit_code == 0
    assert "sales_etl" in result.output
    assert "inventory_etl" not in result.output
