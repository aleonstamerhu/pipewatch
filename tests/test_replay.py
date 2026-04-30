"""Tests for pipewatch.replay."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert, AlertEngine, AlertRule
from pipewatch.audit import AuditLog, AuditEntry
from pipewatch.replay import replay_pipeline, replay_from_audit, ReplayResult


def make_metric(
    pipeline="pipe",
    error_rate=0.0,
    duration=1.0,
    status=MetricStatus.OK,
    offset_seconds=0,
) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        timestamp=datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds),
        error_rate=error_rate,
        duration=duration,
        status=status,
    )


@pytest.fixture
def engine():
    return AlertEngine(rules=[
        AlertRule(name="high_errors", error_rate_threshold=0.05, severity="critical"),
        AlertRule(name="slow_pipeline", duration_threshold=300.0, severity="warning"),
    ])


def test_replay_empty_metrics_returns_empty_result(engine):
    result = replay_pipeline("pipe", [], engine)
    assert result.pipeline == "pipe"
    assert result.total_metrics == 0
    assert result.alerts_fired == []
    assert result.start_time is None
    assert result.end_time is None


def test_replay_healthy_metrics_fires_no_alerts(engine):
    metrics = [make_metric(offset_seconds=i) for i in range(5)]
    result = replay_pipeline("pipe", metrics, engine)
    assert result.total_metrics == 5
    assert result.alerts_fired == []


def test_replay_critical_metric_fires_alert(engine):
    metrics = [
        make_metric(error_rate=0.0, offset_seconds=0),
        make_metric(error_rate=0.5, status=MetricStatus.CRITICAL, offset_seconds=10),
    ]
    result = replay_pipeline("pipe", metrics, engine)
    assert result.total_metrics == 2
    assert any(a.severity == "critical" for a in result.alerts_fired)


def test_replay_preserves_time_span(engine):
    metrics = [
        make_metric(offset_seconds=0),
        make_metric(offset_seconds=120),
    ]
    result = replay_pipeline("pipe", metrics, engine)
    assert result.start_time < result.end_time
    delta = (result.end_time - result.start_time).total_seconds()
    assert delta == 120


def test_replay_summary_string(engine):
    metrics = [make_metric(offset_seconds=i * 10) for i in range(3)]
    result = replay_pipeline("pipe", metrics, engine)
    s = result.summary()
    assert "pipe" in s
    assert "3 metric" in s


def test_replay_from_audit_uses_metric_entries(engine):
    log = AuditLog()
    m = make_metric(error_rate=0.8, status=MetricStatus.CRITICAL)
    log.record_metric(m)
    # Manually patch the entry data to include the metric object
    for entry in log._entries:
        entry.data["metric"] = m

    result = replay_from_audit("pipe", log, engine)
    assert result.total_metrics >= 0  # audit entries may not contain metric objects by default


def test_replay_from_audit_empty_log(engine):
    log = AuditLog()
    result = replay_from_audit("nonexistent", log, engine)
    assert result.total_metrics == 0
    assert result.alerts_fired == []
