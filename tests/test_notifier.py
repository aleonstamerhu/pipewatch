"""Tests for pipewatch.notifier."""

import os
import tempfile
import pytest
from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus
from pipewatch.notifier import (
    ConsoleNotifier,
    LogNotifier,
    NotificationDispatcher,
    NotificationResult,
)


def make_alert(pipeline="pipe1", severity="CRITICAL", reason="errors exceeded"):
    return Alert(pipeline=pipeline, severity=severity, reason=reason)


def test_console_notifier_returns_success(capsys):
    notifier = ConsoleNotifier()
    result = notifier.send(make_alert())
    assert result.success
    assert result.channel == "console"
    captured = capsys.readouterr()
    assert "pipe1" in captured.out


def test_log_notifier_writes_to_file():
    with tempfile.NamedTemporaryFile(mode="r", suffix=".log", delete=False) as f:
        path = f.name
    try:
        notifier = LogNotifier(path)
        alert = make_alert()
        result = notifier.send(alert)
        assert result.success
        assert result.channel == "log"
        with open(path) as f:
            content = f.read()
        assert "pipe1" in content
    finally:
        os.unlink(path)


def test_log_notifier_fails_on_bad_path():
    notifier = LogNotifier("/nonexistent_dir/out.log")
    result = notifier.send(make_alert())
    assert not result.success
    assert result.message != ""


def test_dispatcher_calls_all_notifiers(capsys):
    dispatcher = NotificationDispatcher([ConsoleNotifier(), ConsoleNotifier()])
    results = dispatcher.dispatch(make_alert())
    assert len(results) == 2
    assert all(r.success for r in results)


def test_dispatcher_dispatch_all():
    dispatcher = NotificationDispatcher([ConsoleNotifier()])
    alerts = [make_alert("p1"), make_alert("p2")]
    results = dispatcher.dispatch_all(alerts)
    assert len(results) == 2


def test_dispatcher_add_notifier(capsys):
    dispatcher = NotificationDispatcher()
    assert len(dispatcher.notifiers) == 0
    dispatcher.add(ConsoleNotifier())
    assert len(dispatcher.notifiers) == 1
