"""Tests for pipewatch.trend_cli module."""
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipewatch.trend_cli import trend
from pipewatch.trend import TrendResult
from pipewatch.metrics import MetricStatus
import pytest


@pytest.fixture
def runner():
    return CliRunner()


def make_trend(pipeline="pipe", direction="stable"):
    return TrendResult(
        pipeline=pipeline,
        sample_count=5,
        avg_duration=1.5,
        avg_error_rate=0.01,
        direction=direction,
        latest_status=MetricStatus.OK,
    )


def test_show_no_data(runner):
    with patch("pipewatch.trend_cli.get_collector") as mock_gc:
        mock_gc.return_value.history.return_value = []
        result = runner.invoke(trend, ["show", "mypipe"])
    assert "No data" in result.output


def test_show_with_data(runner):
    with patch("pipewatch.trend_cli.get_collector") as mock_gc:
        mock_gc.return_value.history.return_value = [MagicMock()]
        with patch("pipewatch.trend_cli.analyze_trend", return_value=make_trend("mypipe", "stable")):
            result = runner.invoke(trend, ["show", "mypipe"])
    assert "mypipe" in result.output
    assert "stable" in result.output


def test_all_no_pipelines(runner):
    with patch("pipewatch.trend_cli.get_collector") as mock_gc:
        with patch("pipewatch.trend_cli.analyze_all", return_value=[]):
            result = runner.invoke(trend, ["all"])
    assert "No pipeline" in result.output


def test_all_with_pipelines(runner):
    trends = [make_trend("alpha", "improving"), make_trend("beta", "degrading")]
    with patch("pipewatch.trend_cli.get_collector"):
        with patch("pipewatch.trend_cli.analyze_all", return_value=trends):
            result = runner.invoke(trend, ["all"])
    assert "alpha" in result.output
    assert "beta" in result.output


def test_direction_unknown(runner):
    with patch("pipewatch.trend_cli.get_collector") as mock_gc:
        mock_gc.return_value.history.return_value = []
        result = runner.invoke(trend, ["direction", "pipe"])
    assert "unknown" in result.output


def test_direction_known(runner):
    with patch("pipewatch.trend_cli.get_collector") as mock_gc:
        mock_gc.return_value.history.return_value = [MagicMock()]
        with patch("pipewatch.trend_cli.analyze_trend", return_value=make_trend("pipe", "degrading")):
            result = runner.invoke(trend, ["direction", "pipe"])
    assert "degrading" in result.output
