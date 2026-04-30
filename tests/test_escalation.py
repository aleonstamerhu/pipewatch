"""Tests for pipewatch.escalation."""
from datetime import datetime, timedelta

import pytest

from pipewatch.alerts import Alert, AlertRule
from pipewatch.escalation import EscalationPolicy, EscalationRecord, EscalationStore


def make_alert(pipeline: str = "etl", severity: str = "critical") -> Alert:
    rule = AlertRule(name="high_errors", severity=severity, threshold=0.1)
    return Alert(pipeline=pipeline, rule=rule, value=0.5, message="too many errors")


# --- EscalationPolicy ---

def test_policy_default_values():
    p = EscalationPolicy()
    assert p.escalate_after_seconds == 300
    assert p.max_escalations == 3


def test_policy_rejects_non_positive_seconds():
    with pytest.raises(ValueError, match="escalate_after_seconds"):
        EscalationPolicy(escalate_after_seconds=0)


def test_policy_rejects_zero_max_escalations():
    with pytest.raises(ValueError, match="max_escalations"):
        EscalationPolicy(max_escalations=0)


def test_policy_escalate_after_is_timedelta():
    p = EscalationPolicy(escalate_after_seconds=120)
    assert p.escalate_after == timedelta(seconds=120)


# --- EscalationStore ---

@pytest.fixture
def store():
    return EscalationStore(policy=EscalationPolicy(escalate_after_seconds=60))


def test_first_seen_alert_is_not_escalated(store):
    alert = make_alert()
    assert store.evaluate(alert) is False


def test_alert_not_escalated_before_threshold(store):
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.evaluate(alert, now=now)
    # 30 seconds later — below 60s threshold
    assert store.evaluate(alert, now=now + timedelta(seconds=30)) is False


def test_alert_escalated_after_threshold(store):
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.evaluate(alert, now=now)
    assert store.evaluate(alert, now=now + timedelta(seconds=61)) is True


def test_escalation_count_increments(store):
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.evaluate(alert, now=now)
    store.evaluate(alert, now=now + timedelta(seconds=61))
    record = store.record_for(alert)
    assert record.escalation_count == 1


def test_max_escalations_respected(store):
    store.policy = EscalationPolicy(escalate_after_seconds=10, max_escalations=2)
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.evaluate(alert, now=now)
    store.evaluate(alert, now=now + timedelta(seconds=11))  # escalation 1
    store.evaluate(alert, now=now + timedelta(seconds=22))  # escalation 2
    result = store.evaluate(alert, now=now + timedelta(seconds=33))  # should be capped
    assert result is False
    assert store.record_for(alert).escalation_count == 2


def test_resolve_clears_record(store):
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.evaluate(alert, now=now)
    store.resolve(alert)
    assert store.record_for(alert) is None


def test_different_pipelines_tracked_independently(store):
    a1 = make_alert(pipeline="pipe_a")
    a2 = make_alert(pipeline="pipe_b")
    now = datetime(2024, 1, 1, 12, 0, 0)
    store.evaluate(a1, now=now)
    store.evaluate(a2, now=now)
    assert store.evaluate(a1, now=now + timedelta(seconds=61)) is True
    assert store.evaluate(a2, now=now + timedelta(seconds=61)) is True
    assert len(store.all_records()) == 2
