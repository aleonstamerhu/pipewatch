"""Tests for pipewatch.replay_cli."""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.replay import ReplayResult
from pipewatch.replay_cli import replay


def make_metric(pipeline="pipe", error_rate=0.0, duration=1.0, status=MetricStatus.OK) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        timestamp=datetime(2024, 6, 1, 9, 0, 0),
        error_rate=error_rate,
        duration=duration,
        status=status,
    )


@pytest.fixture
def runner():
    return CliRunner()


def _mock_collector(metrics):
    c = MagicMock()
    c.history.return_value = metrics
    return c


def test_run_no_alerts(runner):
    metrics = [make_metric()]
    result_obj = ReplayResult(
        pipeline="pipe",
        total_metrics=1,
        alerts_fired=[],
        start_time=datetime(2024, 6, 1, 9, 0, 0),
        end_time=datetime(2024, 6, 1, 9, 0, 0),
    )
    with patch("pipewatch.replay_cli._get_collector", return_value=_mock_collector(metrics)), \
         patch("pipewatch.replay_cli.replay_pipeline", return_value=result_obj):
        out = runner.invoke(replay, ["run", "pipe"])
    assert out.exit_code == 0
    assert "No alerts fired" in out.output


def test_run_with_alerts(runner):
    metrics = [make_metric(error_rate=0.9, status=MetricStatus.CRITICAL)]
    alert = Alert(
        rule_name="high_errors",
        pipeline="pipe",
        severity="critical",
        message="Error rate too high",
        triggered_at=datetime(2024, 6, 1, 9, 0, 0),
    )
    result_obj = ReplayResult(
        pipeline="pipe",
        total_metrics=1,
        alerts_fired=[alert],
        start_time=datetime(2024, 6, 1, 9, 0, 0),
        end_time=datetime(2024, 6, 1, 9, 0, 0),
    )
    with patch("pipewatch.replay_cli._get_collector", return_value=_mock_collector(metrics)), \
         patch("pipewatch.replay_cli.replay_pipeline", return_value=result_obj):
        out = runner.invoke(replay, ["run", "pipe"])
    assert out.exit_code == 0
    assert "CRITICAL" in out.output
    assert "high_errors" in out.output


def test_summary_command(runner):
    metrics = [make_metric()]
    result_obj = ReplayResult(
        pipeline="pipe",
        total_metrics=1,
        alerts_fired=[],
        start_time=datetime(2024, 6, 1, 9, 0, 0),
        end_time=datetime(2024, 6, 1, 9, 0, 1),
    )
    with patch("pipewatch.replay_cli._get_collector", return_value=_mock_collector(metrics)), \
         patch("pipewatch.replay_cli.replay_pipeline", return_value=result_obj):
        out = runner.invoke(replay, ["summary", "pipe"])
    assert out.exit_code == 0
    assert "pipe" in out.output
