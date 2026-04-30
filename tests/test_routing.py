"""Tests for pipewatch.routing."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.alerts import Alert
from pipewatch.notifier import NotificationResult
from pipewatch.routing import AlertRouter, RoutingRule
from pipewatch.tagging import TagStore


def make_alert(pipeline: str = "pipe_a", severity: str = "critical") -> Alert:
    return Alert(pipeline=pipeline, message="test alert", severity=severity)


def make_notifier(success: bool = True) -> MagicMock:
    notifier = MagicMock()
    notifier.send.return_value = NotificationResult(success=success, message="ok")
    return notifier


# ---------------------------------------------------------------------------
# RoutingRule.matches
# ---------------------------------------------------------------------------


def test_rule_matches_severity() -> None:
    store = TagStore()
    rule = RoutingRule(notifiers=[], severity="critical")
    assert rule.matches(make_alert(severity="critical"), store) is True
    assert rule.matches(make_alert(severity="warning"), store) is False


def test_rule_matches_tag() -> None:
    store = TagStore()
    store.add("pipe_a", "infra")
    rule = RoutingRule(notifiers=[], tag="infra")
    assert rule.matches(make_alert(pipeline="pipe_a"), store) is True
    assert rule.matches(make_alert(pipeline="pipe_b"), store) is False


def test_rule_matches_tag_and_severity() -> None:
    store = TagStore()
    store.add("pipe_a", "infra")
    rule = RoutingRule(notifiers=[], tag="infra", severity="critical")
    assert rule.matches(make_alert(pipeline="pipe_a", severity="critical"), store) is True
    assert rule.matches(make_alert(pipeline="pipe_a", severity="warning"), store) is False


def test_rule_no_conditions_matches_everything() -> None:
    store = TagStore()
    rule = RoutingRule(notifiers=[])
    assert rule.matches(make_alert(), store) is True


# ---------------------------------------------------------------------------
# AlertRouter.route
# ---------------------------------------------------------------------------


def test_route_uses_first_matching_rule() -> None:
    store = TagStore()
    n1 = make_notifier()
    n2 = make_notifier()
    router = AlertRouter(
        rules=[
            RoutingRule(notifiers=[n1], severity="critical"),
            RoutingRule(notifiers=[n2], severity="critical"),
        ]
    )
    router.route(make_alert(severity="critical"), store)
    n1.send.assert_called_once()
    n2.send.assert_not_called()


def test_route_falls_back_when_no_rule_matches() -> None:
    store = TagStore()
    fallback = make_notifier()
    router = AlertRouter(
        rules=[RoutingRule(notifiers=[make_notifier()], severity="warning")],
        fallback=[fallback],
    )
    router.route(make_alert(severity="critical"), store)
    fallback.send.assert_called_once()


def test_route_all_returns_results_for_every_alert() -> None:
    store = TagStore()
    n = make_notifier()
    router = AlertRouter(fallback=[n])
    alerts = [make_alert(), make_alert(pipeline="pipe_b")]
    results = router.route_all(alerts, store)
    assert len(results) == 2
    assert n.send.call_count == 2
