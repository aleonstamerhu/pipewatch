"""Tests for pipewatch.correlation_cli."""
from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from pipewatch.correlation_cli import correlation
from pipewatch.metrics import PipelineMetric, MetricStatus


def make_metric(pipeline: str, error_count: int = 0) -> PipelineMetric:
    return PipelineMetric(
        pipeline_name=pipeline,
        error_count=error_count,
        duration_seconds=1.0,
        rows_processed=100,
        status=MetricStatus.OK,
    )


@pytest.fixture
def runner():
    return CliRunner()


def _mock_collector(pipelines, histories):
    collector = MagicMock()
    collector.list_pipelines.return_value = pipelines
    collector.history.side_effect = lambda p: histories.get(p, [])
    return collector


def test_all_correlations_too_few_pipelines(runner):
    collector = _mock_collector(["only_one"], {})
    with patch("pipewatch.correlation_cli._get_collector", return_value=collector):
        result = runner.invoke(correlation, ["all"])
    assert result.exit_code == 0
    assert "at least 2" in result.output


def test_all_correlations_not_enough_data(runner):
    histories = {
        "a": [make_metric("a", 1)],
        "b": [make_metric("b", 2)],
    }
    collector = _mock_collector(["a", "b"], histories)
    with patch("pipewatch.correlation_cli._get_collector", return_value=collector):
        result = runner.invoke(correlation, ["all"])
    assert result.exit_code == 0
    assert "Not enough data" in result.output


def test_all_correlations_shows_results(runner):
    histories = {
        "a": [make_metric("a", i) for i in range(5)],
        "b": [make_metric("b", i) for i in range(5)],
    }
    collector = _mock_collector(["a", "b"], histories)
    with patch("pipewatch.correlation_cli._get_collector", return_value=collector):
        result = runner.invoke(correlation, ["all"])
    assert result.exit_code == 0
    assert "a" in result.output
    assert "b" in result.output


def test_pair_missing_pipeline_a(runner):
    collector = _mock_collector([], {"b": [make_metric("b", 1)]})
    with patch("pipewatch.correlation_cli._get_collector", return_value=collector):
        result = runner.invoke(correlation, ["pair", "a", "b"])
    assert result.exit_code == 0
    assert "No data for pipeline: a" in result.output


def test_pair_missing_pipeline_b(runner):
    collector = _mock_collector([], {"a": [make_metric("a", 1)]})
    with patch("pipewatch.correlation_cli._get_collector", return_value=collector):
        result = runner.invoke(correlation, ["pair", "a", "b"])
    assert result.exit_code == 0
    assert "No data for pipeline: b" in result.output


def test_pair_shows_correlation(runner):
    histories = {
        "x": [make_metric("x", i) for i in range(4)],
        "y": [make_metric("y", i * 2) for i in range(4)],
    }
    collector = _mock_collector(["x", "y"], histories)
    with patch("pipewatch.correlation_cli._get_collector", return_value=collector):
        result = runner.invoke(correlation, ["pair", "x", "y"])
    assert result.exit_code == 0
    assert "x" in result.output
    assert "y" in result.output
    assert "r=" in result.output
