"""Alert escalation policy: escalate alerts that remain unresolved beyond a threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.alerts import Alert


@dataclass
class EscalationPolicy:
    """Defines when an alert should be escalated."""
    escalate_after_seconds: int = 300  # 5 minutes default
    max_escalations: int = 3

    def __post_init__(self) -> None:
        if self.escalate_after_seconds <= 0:
            raise ValueError("escalate_after_seconds must be positive")
        if self.max_escalations < 1:
            raise ValueError("max_escalations must be at least 1")

    @property
    def escalate_after(self) -> timedelta:
        return timedelta(seconds=self.escalate_after_seconds)


@dataclass
class EscalationRecord:
    """Tracks escalation state for a single alert key."""
    first_seen: datetime
    last_escalated: Optional[datetime] = None
    escalation_count: int = 0

    def to_dict(self) -> dict:
        return {
            "first_seen": self.first_seen.isoformat(),
            "last_escalated": self.last_escalated.isoformat() if self.last_escalated else None,
            "escalation_count": self.escalation_count,
        }


class EscalationStore:
    """Manages escalation state across alerts."""

    def __init__(self, policy: Optional[EscalationPolicy] = None) -> None:
        self.policy = policy or EscalationPolicy()
        self._records: Dict[str, EscalationRecord] = {}

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}::{alert.rule.name}::{alert.rule.severity}"

    def evaluate(self, alert: Alert, now: Optional[datetime] = None) -> bool:
        """Return True if the alert should be escalated right now."""
        now = now or datetime.utcnow()
        key = self._key(alert)

        if key not in self._records:
            self._records[key] = EscalationRecord(first_seen=now)
            return False

        record = self._records[key]
        if record.escalation_count >= self.policy.max_escalations:
            return False

        reference = record.last_escalated or record.first_seen
        if now - reference >= self.policy.escalate_after:
            record.last_escalated = now
            record.escalation_count += 1
            return True

        return False

    def resolve(self, alert: Alert) -> None:
        """Clear escalation state when an alert is resolved."""
        self._records.pop(self._key(alert), None)

    def record_for(self, alert: Alert) -> Optional[EscalationRecord]:
        return self._records.get(self._key(alert))

    def all_records(self) -> Dict[str, EscalationRecord]:
        return dict(self._records)
