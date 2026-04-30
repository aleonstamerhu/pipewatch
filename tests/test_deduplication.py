"""Tests for pipewatch.deduplication."""

from datetime import datetime, timedelta

import pytest

from pipewatch.alerts import Alert, AlertRule
from pipewatch.deduplication import DeduplicationPolicy, DeduplicationStore
from pipewatch.metrics import MetricStatus


def make_alert(pipeline: str = "etl", name: str = "high_errors", severity: str = "critical") -> Alert:
    rule = AlertRule(name=name, severity=severity, threshold=0.1)
    return Alert(pipeline=pipeline, rule=rule, value=0.5, message="test alert")


@pytest.fixture
def store() -> DeduplicationStore:
    return DeduplicationStore(policy=DeduplicationPolicy(window_seconds=60))


def test_policy_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError):
        DeduplicationPolicy(window_seconds=0)


def test_new_alert_is_not_duplicate(store: DeduplicationStore) -> None:
    alert = make_alert()
    assert store.is_duplicate(alert) is False


def test_alert_is_duplicate_within_window(store: DeduplicationStore) -> None:
    alert = make_alert()
    now = datetime.utcnow()
    store.record(alert, now=now)
    later = now + timedelta(seconds=30)
    assert store.is_duplicate(alert, now=later) is True


def test_alert_not_duplicate_after_window_expires(store: DeduplicationStore) -> None:
    alert = make_alert()
    now = datetime.utcnow()
    store.record(alert, now=now)
    after = now + timedelta(seconds=61)
    assert store.is_duplicate(alert, now=after) is False


def test_different_pipelines_are_independent(store: DeduplicationStore) -> None:
    a1 = make_alert(pipeline="pipe_a")
    a2 = make_alert(pipeline="pipe_b")
    now = datetime.utcnow()
    store.record(a1, now=now)
    assert store.is_duplicate(a2, now=now) is False


def test_deduplicate_filters_repeated_alerts(store: DeduplicationStore) -> None:
    alert = make_alert()
    now = datetime.utcnow()
    first_pass = store.deduplicate([alert], now=now)
    assert len(first_pass) == 1
    second_pass = store.deduplicate([alert], now=now + timedelta(seconds=10))
    assert len(second_pass) == 0


def test_deduplicate_passes_new_alerts(store: DeduplicationStore) -> None:
    a1 = make_alert(pipeline="pipe_a")
    a2 = make_alert(pipeline="pipe_b")
    now = datetime.utcnow()
    result = store.deduplicate([a1, a2], now=now)
    assert len(result) == 2


def test_clear_resets_state(store: DeduplicationStore) -> None:
    alert = make_alert()
    now = datetime.utcnow()
    store.record(alert, now=now)
    store.clear()
    assert store.is_duplicate(alert, now=now) is False
    assert store.seen_keys() == []


def test_seen_keys_returns_recorded_keys(store: DeduplicationStore) -> None:
    a1 = make_alert(pipeline="p1")
    a2 = make_alert(pipeline="p2")
    now = datetime.utcnow()
    store.record(a1, now=now)
    store.record(a2, now=now)
    keys = store.seen_keys()
    assert len(keys) == 2
    assert any("p1" in k for k in keys)
    assert any("p2" in k for k in keys)
