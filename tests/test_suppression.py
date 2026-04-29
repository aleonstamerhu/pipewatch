"""Tests for pipewatch.suppression."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.alerts import Alert
from pipewatch.suppression import (
    SuppressionRule,
    SuppressionStore,
    make_suppression_rule,
)


def make_alert(pipeline: str = "etl", severity: str = "critical") -> Alert:
    return Alert(pipeline=pipeline, severity=severity, message="test alert")


# --- SuppressionRule ---

def test_rule_active_when_no_expiry():
    rule = SuppressionRule(pipeline="etl", severity=None, expires_at=None)
    assert rule.is_active() is True


def test_rule_active_before_expiry():
    future = datetime.utcnow() + timedelta(hours=1)
    rule = SuppressionRule(pipeline="etl", severity=None, expires_at=future)
    assert rule.is_active() is True


def test_rule_inactive_after_expiry():
    past = datetime.utcnow() - timedelta(seconds=1)
    rule = SuppressionRule(pipeline="etl", severity=None, expires_at=past)
    assert rule.is_active() is False


def test_rule_matches_pipeline_and_severity():
    rule = SuppressionRule(pipeline="etl", severity="critical", expires_at=None)
    assert rule.matches(make_alert("etl", "critical")) is True
    assert rule.matches(make_alert("etl", "warning")) is False
    assert rule.matches(make_alert("other", "critical")) is False


def test_rule_matches_any_severity_when_none():
    rule = SuppressionRule(pipeline="etl", severity=None, expires_at=None)
    assert rule.matches(make_alert("etl", "critical")) is True
    assert rule.matches(make_alert("etl", "warning")) is True


# --- SuppressionStore ---

def test_is_suppressed_with_active_rule():
    store = SuppressionStore()
    store.add(make_suppression_rule("etl", severity="critical"))
    assert store.is_suppressed(make_alert("etl", "critical")) is True


def test_not_suppressed_without_matching_rule():
    store = SuppressionStore()
    store.add(make_suppression_rule("other"))
    assert store.is_suppressed(make_alert("etl", "critical")) is False


def test_not_suppressed_after_expiry():
    past = datetime.utcnow() - timedelta(seconds=10)
    rule = SuppressionRule(pipeline="etl", severity=None, expires_at=past)
    store = SuppressionStore()
    store.add(rule)
    assert store.is_suppressed(make_alert("etl")) is False


def test_remove_returns_count():
    store = SuppressionStore()
    store.add(make_suppression_rule("etl", severity="critical"))
    store.add(make_suppression_rule("etl", severity="critical"))
    removed = store.remove("etl", severity="critical")
    assert removed == 2


def test_purge_expired_removes_old_rules():
    past = datetime.utcnow() - timedelta(seconds=5)
    store = SuppressionStore()
    store.add(SuppressionRule(pipeline="etl", severity=None, expires_at=past))
    store.add(make_suppression_rule("other"))  # permanent
    removed = store.purge_expired()
    assert removed == 1
    assert len(store.active_rules()) == 1


def test_make_suppression_rule_with_duration():
    rule = make_suppression_rule("etl", duration_minutes=30, reason="maintenance")
    assert rule.pipeline == "etl"
    assert rule.expires_at is not None
    assert rule.reason == "maintenance"
