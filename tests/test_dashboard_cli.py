"""Tests for dashboard CLI commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipewatch.dashboard_cli import dashboard
from pipewatch.reporter import PipelineReport
from pipewatch.metrics import PipelineMetric, MetricStatus
from datetime import datetime


def make_metric(pipeline="pipe1"):
    return PipelineMetric(
        pipeline_name=pipeline,
        timestamp=datetime(2024, 1, 1),
        record_count=50,
        error_rate=0.0,
        duration_seconds=2.0,
    )


@pytest.fixture
def runner():
    return CliRunner()


def test_show_no_pipelines(runner):
    result = runner.invoke(dashboard, ["show"])
    assert result.exit_code == 0
    assert "No pipelines specified" in result.output


def test_show_renders_pipeline(runner):
    metric = make_metric()
    report = PipelineReport(latest=metric, alerts=[], history=[])
    with patch("pipewatch.dashboard_cli._reporter") as mock_reporter, \
         patch("pipewatch.dashboard_cli._dashboard") as mock_dash:
        mock_dash.render.return_value = "pipe1  OK\n"
        result = runner.invoke(dashboard, ["show", "pipe1"])
        mock_dash.render.assert_called_once_with(["pipe1"])
        assert "pipe1" in result.output


def test_summary_command(runner):
    metric = make_metric()
    report = PipelineReport(latest=metric, alerts=[], history=[])
    with patch("pipewatch.dashboard_cli._reporter") as mock_reporter:
        mock_reporter.report.return_value = report
        result = runner.invoke(dashboard, ["summary", "pipe1"])
        assert "pipe1" in result.output
        assert "Status" in result.output


def test_summary_no_alerts(runner):
    metric = make_metric()
    report = PipelineReport(latest=metric, alerts=[], history=[])
    with patch("pipewatch.dashboard_cli._reporter") as mock_reporter:
        mock_reporter.report.return_value = report
        result = runner.invoke(dashboard, ["summary", "pipe1"])
        assert "none" in result.output
