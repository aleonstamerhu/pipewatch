"""Tests for pipewatch CLI commands."""
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipewatch.cli import cli
from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.reporter import PipelineReport
from datetime import datetime


def make_metric(pipeline_id="pipe1"):
    return PipelineMetric(
        pipeline_id=pipeline_id,
        timestamp=datetime.utcnow(),
        duration_seconds=5.0,
        error_count=0,
        rows_processed=10,
        status=MetricStatus.OK,
    )


def test_record_command_ok():
    runner = CliRunner()
    result = runner.invoke(cli, ["record", "mypipe", "--duration", "5", "--errors", "0"])
    assert result.exit_code == 0
    assert "mypipe" in result.output


def test_record_command_critical_alert():
    runner = CliRunner()
    result = runner.invoke(cli, ["record", "mypipe", "--errors", "3"])
    assert result.exit_code == 0
    assert "ALERT" in result.output


def test_status_command():
    runner = CliRunner()
    runner.invoke(cli, ["record", "mypipe", "--duration", "2"])
    result = runner.invoke(cli, ["status", "mypipe"])
    assert result.exit_code == 0
    assert "mypipe" in result.output


def test_list_command_no_pipelines():
    """Isolated test — uses fresh module state via patching."""
    runner = CliRunner()
    with patch("pipewatch.cli._collector") as mock_col:
        mock_col.pipelines.return_value = []
        result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No pipelines" in result.output


def test_list_command_with_pipelines():
    runner = CliRunner()
    with patch("pipewatch.cli._collector") as mock_col, \
         patch("pipewatch.cli._reporter") as mock_rep:
        mock_col.pipelines.return_value = ["alpha", "beta"]
        mock_rep.report.return_value = PipelineReport(status="ok", summary="All good")
        result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output
