"""Tests for pipewatch.throttle."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from click.testing import CliRunner

from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus
from pipewatch.throttle import AlertThrottler, ThrottlePolicy, ThrottleState


def make_alert(pipeline: str = "pipe_a", rule: str = "error_rate") -> Alert:
    return Alert(
        pipeline=pipeline,
        rule_name=rule,
        severity="critical",
        message=f"{pipeline} triggered {rule}",
        metric_value=0.5,
    )


# --- ThrottlePolicy ---

def test_policy_default_cooldown() -> None:
    p = ThrottlePolicy()
    assert p.cooldown_seconds == 300


def test_policy_rejects_negative_cooldown() -> None:
    with pytest.raises(ValueError):
        ThrottlePolicy(cooldown_seconds=-1)


# --- ThrottleState ---

def test_new_alert_is_not_suppressed() -> None:
    state = ThrottleState()
    policy = ThrottlePolicy(cooldown_seconds=60)
    alert = make_alert()
    assert state.is_suppressed(alert, policy) is False


def test_alert_suppressed_within_cooldown() -> None:
    state = ThrottleState()
    policy = ThrottlePolicy(cooldown_seconds=60)
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    state.record(alert, now=now)
    later = now + timedelta(seconds=30)
    assert state.is_suppressed(alert, policy, now=later) is True


def test_alert_not_suppressed_after_cooldown() -> None:
    state = ThrottleState()
    policy = ThrottlePolicy(cooldown_seconds=60)
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    state.record(alert, now=now)
    later = now + timedelta(seconds=61)
    assert state.is_suppressed(alert, policy, now=later) is False


def test_reset_clears_specific_key() -> None:
    state = ThrottleState()
    policy = ThrottlePolicy(cooldown_seconds=300)
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    state.record(alert, now=now)
    state.reset(alert.pipeline, alert.rule_name)
    assert state.is_suppressed(alert, policy, now=now) is False


def test_clear_removes_all_state() -> None:
    state = ThrottleState()
    policy = ThrottlePolicy(cooldown_seconds=300)
    now = datetime(2024, 1, 1, 12, 0, 0)
    for name in ("pipe_a", "pipe_b"):
        state.record(make_alert(pipeline=name), now=now)
    state.clear()
    assert state._last_sent == {}


# --- AlertThrottler ---

def test_throttler_allows_first_alert() -> None:
    throttler = AlertThrottler(ThrottlePolicy(cooldown_seconds=60))
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    result = throttler.filter([alert], now=now)
    assert result == [alert]


def test_throttler_suppresses_duplicate() -> None:
    throttler = AlertThrottler(ThrottlePolicy(cooldown_seconds=60))
    alert = make_alert()
    now = datetime(2024, 1, 1, 12, 0, 0)
    throttler.filter([alert], now=now)
    result = throttler.filter([alert], now=now + timedelta(seconds=10))
    assert result == []


def test_throttler_allows_different_pipelines() -> None:
    throttler = AlertThrottler(ThrottlePolicy(cooldown_seconds=300))
    now = datetime(2024, 1, 1, 12, 0, 0)
    a1 = make_alert(pipeline="pipe_a")
    a2 = make_alert(pipeline="pipe_b")
    result = throttler.filter([a1, a2], now=now)
    assert len(result) == 2
