"""Tests for pipewatch.reporter."""

from unittest.mock import MagicMock

import pytest

from pipewatch.alerts import Alert, AlertEngine, AlertRule
from pipewatch.collector import MetricsCollector
from pipewatch.metrics import MetricStatus, PipelineMetric, compute_status
from pipewatch.reporter import Reporter


def make_metric(name="etl", duration=1.0, errors=0, rows=100) -> PipelineMetric:
    m = PipelineMetric(pipeline_name=name, duration_seconds=duration, error_count=errors, rows_processed=rows)
    m.status = compute_status(m)
    return m


@pytest.fixture
def collector():
    return MetricsCollector(max_history=10)


@pytest.fixture
def engine():
    rules = [
        AlertRule(name="high_errors", metric_field="error_count", threshold=5, level="critical"),
        AlertRule(name="slow_pipeline", metric_field="duration_seconds", threshold=30.0, level="warning"),
    ]
    return AlertEngine(rules=rules)


@pytest.fixture
def reporter(collector, engine):
    return Reporter(collector=collector, alert_engine=engine)


def test_report_unknown_when_no_data(reporter):
    report = reporter.report("missing_pipeline")
    assert report.status == MetricStatus.UNKNOWN
    assert report.history_count == 0
    assert report.alerts == []


def test_report_reflects_latest_metric(reporter, collector):
    m = make_metric(name="etl", errors=0, duration=2.0)
    collector.record(m)
    report = reporter.report("etl")
    assert report.latest_metric is m
    assert report.history_count == 1
    assert report.status == MetricStatus.OK


def test_report_includes_alerts_on_critical(reporter, collector):
    m = make_metric(name="etl", errors=10)
    collector.record(m)
    report = reporter.report("etl")
    assert any(a.level == "critical" for a in report.alerts)


def test_summary_contains_pipeline_name(reporter, collector):
    collector.record(make_metric(name="etl"))
    report = reporter.report("etl")
    summary = report.summary()
    assert "etl" in summary
    assert "OK" in summary.upper()


def test_report_all_covers_all_pipelines(reporter, collector):
    collector.record(make_metric(name="pipe_a"))
    collector.record(make_metric(name="pipe_b"))
    reports = reporter.report_all()
    names = {r.pipeline_name for r in reports}
    assert "pipe_a" in names
    assert "pipe_b" in names
