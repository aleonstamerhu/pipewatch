"""Tests for retention policy logic."""
import pytest
from datetime import datetime, timedelta
from pipewatch.audit import AuditLog, AuditEntry
from pipewatch.retention import RetentionPolicy, apply_retention, retention_summary


def make_entry(pipeline: str, days_ago: int = 0) -> AuditEntry:
    return AuditEntry(
        timestamp=datetime.utcnow() - timedelta(days=days_ago),
        pipeline=pipeline,
        event_type="metric",
        details={},
    )


def make_log(*entries: AuditEntry) -> AuditLog:
    log = AuditLog()
    log.entries = list(entries)
    return log


def test_policy_rejects_invalid_age():
    with pytest.raises(ValueError):
        RetentionPolicy(max_age_days=0)


def test_policy_rejects_invalid_entries():
    with pytest.raises(ValueError):
        RetentionPolicy(max_entries=-1)


def test_is_expired_old_entry():
    policy = RetentionPolicy(max_age_days=3)
    entry = make_entry("p", days_ago=5)
    assert policy.is_expired(entry) is True


def test_is_not_expired_recent_entry():
    policy = RetentionPolicy(max_age_days=3)
    entry = make_entry("p", days_ago=1)
    assert policy.is_expired(entry) is False


def test_apply_retention_removes_expired():
    log = make_log(make_entry("a", days_ago=10), make_entry("b", days_ago=1))
    policy = RetentionPolicy(max_age_days=7)
    removed = apply_retention(log, policy)
    assert removed == 1
    assert len(log.entries) == 1
    assert log.entries[0].pipeline == "b"


def test_apply_retention_caps_max_entries():
    log = make_log(*[make_entry("p", days_ago=0) for _ in range(10)])
    policy = RetentionPolicy(max_age_days=30, max_entries=5)
    removed = apply_retention(log, policy)
    assert removed == 5
    assert len(log.entries) == 5


def test_retention_summary_no_changes():
    log = make_log(make_entry("p", days_ago=1))
    policy = RetentionPolicy(max_age_days=7, max_entries=100)
    s = retention_summary(log, policy)
    assert s["total"] == 1
    assert s["expired"] == 0
    assert s["would_remove"] == 0


def test_retention_summary_counts_expired():
    log = make_log(make_entry("a", days_ago=10), make_entry("b", days_ago=1))
    policy = RetentionPolicy(max_age_days=5)
    s = retention_summary(log, policy)
    assert s["expired"] == 1
    assert s["total"] == 2
