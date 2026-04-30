"""Alert deduplication: suppress repeated identical alerts within a time window."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.alerts import Alert


@dataclass
class DeduplicationPolicy:
    window_seconds: int = 300  # 5 minutes default

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    @property
    def window(self) -> timedelta:
        return timedelta(seconds=self.window_seconds)


@dataclass
class DeduplicationStore:
    policy: DeduplicationPolicy = field(default_factory=DeduplicationPolicy)
    _seen: Dict[str, datetime] = field(default_factory=dict, init=False, repr=False)

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}:{alert.rule.name}:{alert.rule.severity}"

    def is_duplicate(self, alert: Alert, now: Optional[datetime] = None) -> bool:
        """Return True if an identical alert was already seen within the window."""
        now = now or datetime.utcnow()
        key = self._key(alert)
        last_seen = self._seen.get(key)
        if last_seen is None:
            return False
        return (now - last_seen) < self.policy.window

    def record(self, alert: Alert, now: Optional[datetime] = None) -> None:
        """Mark an alert as seen at the given time."""
        now = now or datetime.utcnow()
        self._seen[self._key(alert)] = now

    def deduplicate(self, alerts: List[Alert], now: Optional[datetime] = None) -> List[Alert]:
        """Filter a list of alerts, returning only non-duplicate ones and recording them."""
        now = now or datetime.utcnow()
        unique: List[Alert] = []
        for alert in alerts:
            if not self.is_duplicate(alert, now=now):
                self.record(alert, now=now)
                unique.append(alert)
        return unique

    def clear(self) -> None:
        """Reset all deduplication state."""
        self._seen.clear()

    def seen_keys(self) -> List[str]:
        """Return all currently tracked deduplication keys."""
        return list(self._seen.keys())
