"""Tests for pipewatch/grouping_cli.py"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.grouping import GroupSummary
from pipewatch.grouping_cli import grouping


def make_summary(tag, pipelines, ok=1, warn=0, crit=0, unk=0):
    return GroupSummary(
        tag=tag,
        pipelines=pipelines,
        ok_count=ok,
        warning_count=warn,
        critical_count=crit,
        unknown_count=unk,
    )


@pytest.fixture
def runner():
    return CliRunner()


def test_show_no_pipelines(runner):
    with patch("pipewatch.grouping_cli.group_by_tag", return_value=None):
        result = runner.invoke(grouping, ["show", "missing-tag"])
    assert result.exit_code == 0
    assert "No pipelines found" in result.output


def test_show_renders_summary(runner):
    summary = make_summary("team-alpha", ["pipeline_a", "pipeline_b"], ok=2)
    mock_collector = MagicMock()
    mock_metric = MagicMock()
    mock_metric.status = MetricStatus.OK
    mock_collector.latest.return_value = mock_metric

    with patch("pipewatch.grouping_cli.group_by_tag", return_value=summary), \
         patch("pipewatch.grouping_cli._get_collector", return_value=mock_collector):
        result = runner.invoke(grouping, ["show", "team-alpha"])
    assert result.exit_code == 0
    assert "team-alpha" in result.output
    assert "pipeline_a" in result.output


def test_all_no_tags(runner):
    with patch("pipewatch.grouping_cli.group_all", return_value=[]):
        result = runner.invoke(grouping, ["all"])
    assert result.exit_code == 0
    assert "No tagged pipelines" in result.output


def test_all_renders_multiple_groups(runner):
    summaries = [
        make_summary("team-alpha", ["a"], ok=1),
        make_summary("team-beta", ["b"], crit=1),
    ]
    with patch("pipewatch.grouping_cli.group_all", return_value=summaries):
        result = runner.invoke(grouping, ["all"])
    assert result.exit_code == 0
    assert "team-alpha" in result.output
    assert "team-beta" in result.output


def test_dominant_command_prints_status(runner):
    summary = make_summary("team-alpha", ["a"], crit=1)
    with patch("pipewatch.grouping_cli.group_by_tag", return_value=summary):
        result = runner.invoke(grouping, ["dominant", "team-alpha"])
    assert result.exit_code == 0
    assert "critical" in result.output.lower()


def test_dominant_command_no_pipelines(runner):
    with patch("pipewatch.grouping_cli.group_by_tag", return_value=None):
        result = runner.invoke(grouping, ["dominant", "ghost-tag"])
    assert result.exit_code == 0
    assert "No pipelines found" in result.output
