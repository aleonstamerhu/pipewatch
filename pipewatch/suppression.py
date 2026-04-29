"""Alert suppression rules — silence alerts matching pipeline/severity criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from pipewatch.alerts import Alert


@dataclass
class SuppressionRule:
    pipeline: str
    severity: Optional[str]  # None means match any severity
    expires_at: Optional[datetime]  # None means never expires
    reason: str = ""

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return True
        return (now or datetime.utcnow()) < self.expires_at

    def matches(self, alert: Alert) -> bool:
        if alert.pipeline != self.pipeline:
            return False
        if self.severity is not None and alert.severity != self.severity:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "severity": self.severity,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "reason": self.reason,
        }


@dataclass
class SuppressionStore:
    _rules: list[SuppressionRule] = field(default_factory=list)

    def add(self, rule: SuppressionRule) -> None:
        self._rules.append(rule)

    def remove(self, pipeline: str, severity: Optional[str] = None) -> int:
        before = len(self._rules)
        self._rules = [
            r for r in self._rules
            if not (r.pipeline == pipeline and r.severity == severity)
        ]
        return before - len(self._rules)

    def is_suppressed(self, alert: Alert, now: Optional[datetime] = None) -> bool:
        ts = now or datetime.utcnow()
        return any(r.is_active(ts) and r.matches(alert) for r in self._rules)

    def active_rules(self, now: Optional[datetime] = None) -> list[SuppressionRule]:
        ts = now or datetime.utcnow()
        return [r for r in self._rules if r.is_active(ts)]

    def purge_expired(self, now: Optional[datetime] = None) -> int:
        ts = now or datetime.utcnow()
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.is_active(ts)]
        return before - len(self._rules)


def make_suppression_rule(
    pipeline: str,
    severity: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    reason: str = "",
) -> SuppressionRule:
    expires_at = (
        datetime.utcnow() + timedelta(minutes=duration_minutes)
        if duration_minutes is not None
        else None
    )
    return SuppressionRule(
        pipeline=pipeline,
        severity=severity,
        expires_at=expires_at,
        reason=reason,
    )
