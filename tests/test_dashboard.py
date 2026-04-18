"""Tests for the terminal dashboard."""
import pytest
from unittest.mock import MagicMock
from pipewatch.dashboard import Dashboard, DashboardRow
from pipewatch.reporter import PipelineReport
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from datetime import datetime


def make_metric(pipeline="pipe1", error_rate=0.0, duration=1.5, records=100):
    return PipelineMetric(
        pipeline_name=pipeline,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        record_count=records,
        error_rate=error_rate,
        duration_seconds=duration,
    )


@pytest.fixture
def reporter():
    return MagicMock()


@pytest.fixture
def dashboard(reporter):
    return Dashboard(reporter)


def test_get_rows_healthy(dashboard, reporter):
    metric = make_metric()
    reporter.report.return_value = PipelineReport(latest=metric, alerts=[], history=[])
    rows = dashboard.get_rows(["pipe1"])
    assert len(rows) == 1
    assert rows[0].pipeline == "pipe1"
    assert rows[0].alert_count == 0


def test_get_rows_with_alerts(dashboard, reporter):
    metric = make_metric(error_rate=0.5)
    alert = MagicMock(spec=Alert)
    reporter.report.return_value = PipelineReport(latest=metric, alerts=[alert, alert], history=[])
    rows = dashboard.get_rows(["pipe1"])
    assert rows[0].alert_count == 2


def test_render_empty(dashboard):
    result = dashboard.render([])
    assert "No pipelines" in result


def test_render_contains_pipeline_name(dashboard, reporter):
    metric = make_metric(pipeline="etl_main")
    reporter.report.return_value = PipelineReport(latest=metric, alerts=[], history=[])
    result = dashboard.render(["etl_main"])
    assert "etl_main" in result


def test_render_shows_header(dashboard, reporter):
    metric = make_metric()
    reporter.report.return_value = PipelineReport(latest=metric, alerts=[], history=[])
    result = dashboard.render(["pipe1"])
    assert "Pipeline" in result
    assert "Status" in result
    assert "Alerts" in result


def test_get_rows_no_metric(dashboard, reporter):
    reporter.report.return_value = PipelineReport(latest=None, alerts=[], history=[])
    rows = dashboard.get_rows(["ghost"])
    assert rows[0].record_count == 0
    assert rows[0].error_rate == 0.0
