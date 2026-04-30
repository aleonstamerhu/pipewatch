"""Alert routing: direct alerts to notifiers based on pipeline tags and severity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.alerts import Alert
from pipewatch.notifier import BaseNotifier, NotificationResult
from pipewatch.tagging import TagStore


@dataclass
class RoutingRule:
    """Maps a condition (tag and/or severity) to a list of notifiers."""

    notifiers: List[BaseNotifier]
    tag: Optional[str] = None
    severity: Optional[str] = None  # "warning" | "critical"

    def matches(self, alert: Alert, tag_store: TagStore) -> bool:
        """Return True if this rule applies to *alert*."""
        if self.severity and alert.severity != self.severity:
            return False
        if self.tag:
            tags = tag_store.get(alert.pipeline)
            if self.tag.lower() not in tags:
                return False
        return True


@dataclass
class AlertRouter:
    """Routes an alert to the first matching rule's notifiers (or a fallback)."""

    rules: List[RoutingRule] = field(default_factory=list)
    fallback: List[BaseNotifier] = field(default_factory=list)

    def add_rule(self, rule: RoutingRule) -> None:
        self.rules.append(rule)

    def route(self, alert: Alert, tag_store: TagStore) -> List[NotificationResult]:
        """Send *alert* via the first matching rule; fall back to default notifiers."""
        for rule in self.rules:
            if rule.matches(alert, tag_store):
                return [n.send(alert) for n in rule.notifiers]
        return [n.send(alert) for n in self.fallback]

    def route_all(
        self, alerts: List[Alert], tag_store: TagStore
    ) -> List[NotificationResult]:
        """Route every alert in *alerts* and return all results."""
        results: List[NotificationResult] = []
        for alert in alerts:
            results.extend(self.route(alert, tag_store))
        return results
