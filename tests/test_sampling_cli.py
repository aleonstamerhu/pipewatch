"""Tests for pipewatch.sampling_cli."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pipewatch.collector import MetricsCollector
from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.sampling_cli import sampling


def make_metric(
    pipeline: str = "pipe",
    offset_seconds: float = 0.0,
) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        status=MetricStatus.OK,
        error_rate=0.0,
        duration_seconds=1.0,
        timestamp=datetime(2024, 1, 1) + timedelta(seconds=offset_seconds),
    )


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _mock_collector(metrics_by_pipeline: dict) -> MetricsCollector:
    c = MetricsCollector()
    for pipeline, metrics in metrics_by_pipeline.items():
        for m in metrics:
            c.record(m)
    return c


def test_show_no_data(runner: CliRunner) -> None:
    c = MetricsCollector()
    with patch("pipewatch.sampling_cli._get_collector", return_value=c):
        result = runner.invoke(sampling, ["show", "missing_pipe"])
    assert result.exit_code == 0
    assert "No data" in result.output


def test_show_with_data(runner: CliRunner) -> None:
    metrics = [make_metric("alpha", offset_seconds=float(i)) for i in range(8)]
    c = _mock_collector({"alpha": metrics})
    with patch("pipewatch.sampling_cli._get_collector", return_value=c):
        result = runner.invoke(sampling, ["show", "alpha", "--max-samples", "5"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "5/8" in result.output


def test_all_no_pipelines(runner: CliRunner) -> None:
    c = MetricsCollector()
    with patch("pipewatch.sampling_cli._get_collector", return_value=c):
        result = runner.invoke(sampling, ["all"])
    assert result.exit_code == 0
    assert "No pipelines" in result.output


def test_all_multiple_pipelines(runner: CliRunner) -> None:
    metrics_a = [make_metric("a", offset_seconds=float(i)) for i in range(4)]
    metrics_b = [make_metric("b", offset_seconds=float(i)) for i in range(2)]
    c = _mock_collector({"a": metrics_a, "b": metrics_b})
    with patch("pipewatch.sampling_cli._get_collector", return_value=c):
        result = runner.invoke(sampling, ["all", "--max-samples", "3"])
    assert result.exit_code == 0
    assert "a" in result.output
    assert "b" in result.output
