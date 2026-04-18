"""Tests for pipewatch.audit."""

from datetime import datetime
from pipewatch.audit import AuditLog, AuditEntry
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert


def make_metric(pipeline="etl", errors=0, duration=1.0, rows=100):
    return PipelineMetric(
        pipeline_name=pipeline,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        rows_processed=rows,
        error_count=errors,
        duration_seconds=duration,
        status=MetricStatus.OK if errors == 0 else MetricStatus.CRITICAL,
    )


def make_alert(pipeline="etl", severity="critical", message="Something broke"):
    return Alert(
        pipeline_name=pipeline,
        severity=severity,
        message=message,
        triggered_at=datetime(2024, 1, 1, 12, 1, 0),
    )


def test_record_metric_creates_entry():
    log = AuditLog()
    log.record_metric(make_metric())
    entries = log.entries()
    assert len(entries) == 1
    assert entries[0].event_type == "metric"
    assert entries[0].pipeline == "etl"
    assert entries[0].status == MetricStatus.OK.value


def test_record_alert_creates_entry():
    log = AuditLog()
    log.record_alert(make_alert())
    entries = log.entries()
    assert len(entries) == 1
    assert entries[0].event_type == "alert"
    assert entries[0].severity == "critical" or entries[0].status == "critical"


def test_filter_by_pipeline():
    log = AuditLog()
    log.record_metric(make_metric(pipeline="pipe_a"))
    log.record_metric(make_metric(pipeline="pipe_b"))
    assert len(log.entries(pipeline="pipe_a")) == 1
    assert len(log.entries(pipeline="pipe_b")) == 1


def test_max_entries_capped():
    log = AuditLog(max_entries=5)
    for _ in range(10):
        log.record_metric(make_metric())
    assert len(log.entries()) == 5


def test_clear_removes_all_entries():
    log = AuditLog()
    log.record_metric(make_metric())
    log.clear()
    assert log.entries() == []


def test_to_dict_has_expected_keys():
    log = AuditLog()
    log.record_metric(make_metric())
    d = log.entries()[0].to_dict()
    assert set(d.keys()) == {"timestamp", "pipeline", "event_type", "status", "detail"}
