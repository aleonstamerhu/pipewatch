"""Tests for pipewatch.digest."""

from datetime import datetime

import pytest

from pipewatch.collector import MetricsCollector
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.digest import build_digest, DigestEntry, Digest


def make_metric(
    pipeline: str = "pipe",
    status: MetricStatus = MetricStatus.OK,
    error_rate: float = 0.0,
    duration: float = 1.0,
) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        status=status,
        error_rate=error_rate,
        duration_seconds=duration,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture()
def collector() -> MetricsCollector:
    return MetricsCollector()


def test_empty_collector_returns_empty_digest(collector):
    digest = build_digest(collector)
    assert digest.total_pipelines == 0
    assert digest.entries == []
    assert digest.healthy_count == 0


def test_single_healthy_pipeline(collector):
    collector.record(make_metric("alpha", MetricStatus.OK, error_rate=0.0, duration=0.5))
    digest = build_digest(collector)
    assert digest.total_pipelines == 1
    assert digest.healthy_count == 1
    assert digest.critical_count == 0
    assert digest.entries[0].pipeline == "alpha"


def test_critical_pipeline_counted(collector):
    collector.record(make_metric("beta", MetricStatus.CRITICAL, error_rate=0.9, duration=30.0))
    digest = build_digest(collector)
    assert digest.critical_count == 1
    assert digest.healthy_count == 0


def test_alert_count_reflected_in_entry(collector):
    collector.record(make_metric("gamma", MetricStatus.WARNING, error_rate=0.2))
    alerts = [
        Alert(pipeline="gamma", severity="warning", message="slow"),
        Alert(pipeline="gamma", severity="warning", message="errors"),
    ]
    digest = build_digest(collector, alerts=alerts)
    entry = next(e for e in digest.entries if e.pipeline == "gamma")
    assert entry.alert_count == 2


def test_no_alerts_for_unrelated_pipeline(collector):
    collector.record(make_metric("delta", MetricStatus.OK))
    alerts = [Alert(pipeline="other", severity="critical", message="boom")]
    digest = build_digest(collector, alerts=alerts)
    entry = digest.entries[0]
    assert entry.alert_count == 0


def test_entries_sorted_by_health_score_ascending(collector):
    collector.record(make_metric("good", MetricStatus.OK, error_rate=0.0, duration=0.1))
    collector.record(make_metric("bad", MetricStatus.CRITICAL, error_rate=1.0, duration=60.0))
    digest = build_digest(collector)
    scores = [e.health_score for e in digest.entries]
    assert scores == sorted(scores)


def test_digest_summary_contains_counts(collector):
    collector.record(make_metric("p1", MetricStatus.OK))
    collector.record(make_metric("p2", MetricStatus.CRITICAL, error_rate=0.95))
    digest = build_digest(collector)
    summary = digest.summary()
    assert "Pipelines: 2" in summary
    assert "UTC" in summary


def test_entry_to_dict_keys(collector):
    collector.record(make_metric("zeta", MetricStatus.OK, error_rate=0.01, duration=2.5))
    digest = build_digest(collector)
    d = digest.entries[0].to_dict()
    assert set(d.keys()) == {"pipeline", "health_score", "status", "error_rate", "avg_duration", "alert_count"}
    assert d["pipeline"] == "zeta"
