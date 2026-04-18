"""Tests for the alert engine and alert rules."""

import pytest
from pipewatch.metrics import MetricStatus, PipelineMetric, compute_status
from pipewatch.alerts import Alert, AlertEngine, AlertRule


def make_metric(pipeline="etl_main", error_count=0, duration=1.0, row_count=100):
    m = PipelineMetric(
        pipeline_name=pipeline,
        error_count=error_count,
        duration_seconds=duration,
        row_count=row_count,
    )
    m.status = compute_status(m)
    return m


@pytest.fixture
def engine():
    e = AlertEngine()
    e.add_rule(AlertRule(
        name="high_errors",
        pipeline="etl_main",
        condition=lambda m: m.error_count > 0,
        message="Errors detected in pipeline",
        severity="critical",
    ))
    e.add_rule(AlertRule(
        name="slow_pipeline",
        pipeline="etl_main",
        condition=lambda m: m.duration_seconds > 30,
        message="Pipeline exceeded duration threshold",
        severity="warning",
    ))
    return e


def test_no_alerts_when_healthy(engine):
    metric = make_metric(error_count=0, duration=10.0)
    alerts = engine.evaluate(metric)
    assert alerts == []


def test_critical_alert_on_errors(engine):
    metric = make_metric(error_count=3)
    alerts = engine.evaluate(metric)
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    assert alerts[0].rule_name == "high_errors"


def test_warning_alert_on_slow_pipeline(engine):
    metric = make_metric(duration=60.0)
    alerts = engine.evaluate(metric)
    assert len(alerts) == 1
    assert alerts[0].severity == "warning"


def test_multiple_alerts_fired(engine):
    metric = make_metric(error_count=2, duration=45.0)
    alerts = engine.evaluate(metric)
    assert len(alerts) == 2


def test_rule_scoped_to_pipeline(engine):
    metric = make_metric(pipeline="other_pipeline", error_count=5)
    alerts = engine.evaluate(metric)
    assert alerts == []


def test_alert_str_representation(engine):
    metric = make_metric(error_count=1)
    alerts = engine.evaluate(metric)
    assert "CRITICAL" in str(alerts[0])
    assert "etl_main" in str(alerts[0])


def test_evaluate_all(engine):
    metrics = [make_metric(error_count=1), make_metric(pipeline="other")]
    alerts = engine.evaluate_all(metrics)
    assert len(alerts) == 1
