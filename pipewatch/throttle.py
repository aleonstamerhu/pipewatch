"""Alert throttling: suppress repeated alerts within a cooldown window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.alerts import Alert


@dataclass
class ThrottlePolicy:
    """Defines how long to suppress duplicate alerts for a pipeline/rule pair."""

    cooldown_seconds: int = 300

    def __post_init__(self) -> None:
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")

    @property
    def cooldown(self) -> timedelta:
        return timedelta(seconds=self.cooldown_seconds)


@dataclass
class ThrottleState:
    """Tracks the last time an alert was forwarded for a given key."""

    _last_sent: Dict[str, datetime] = field(default_factory=dict)

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}::{alert.rule_name}"

    def is_suppressed(self, alert: Alert, policy: ThrottlePolicy, now: Optional[datetime] = None) -> bool:
        """Return True if the alert should be suppressed based on the cooldown."""
        now = now or datetime.utcnow()
        key = self._key(alert)
        last = self._last_sent.get(key)
        if last is None:
            return False
        return (now - last) < policy.cooldown

    def record(self, alert: Alert, now: Optional[datetime] = None) -> None:
        """Mark an alert as sent at *now*."""
        now = now or datetime.utcnow()
        self._last_sent[self._key(alert)] = now

    def reset(self, pipeline: str, rule_name: str) -> None:
        """Remove throttle state for a specific pipeline/rule pair."""
        key = f"{pipeline}::{rule_name}"
        self._last_sent.pop(key, None)

    def clear(self) -> None:
        """Remove all throttle state."""
        self._last_sent.clear()


class AlertThrottler:
    """Wraps ThrottleState + ThrottlePolicy to filter a list of alerts."""

    def __init__(self, policy: Optional[ThrottlePolicy] = None) -> None:
        self.policy = policy or ThrottlePolicy()
        self.state = ThrottleState()

    def filter(self, alerts: list[Alert], now: Optional[datetime] = None) -> list[Alert]:
        """Return only alerts that are not currently throttled, and record them."""
        now = now or datetime.utcnow()
        allowed: list[Alert] = []
        for alert in alerts:
            if not self.state.is_suppressed(alert, self.policy, now=now):
                self.state.record(alert, now=now)
                allowed.append(alert)
        return allowed
