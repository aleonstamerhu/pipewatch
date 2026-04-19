"""Retention policy for pruning old audit and metric history."""
from datetime import datetime, timedelta
from typing import List
from pipewatch.audit import AuditEntry, AuditLog


class RetentionPolicy:
    """Defines how long entries should be kept."""

    def __init__(self, max_age_days: int = 7, max_entries: int = 1000):
        if max_age_days <= 0:
            raise ValueError("max_age_days must be positive")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self.max_age_days = max_age_days
        self.max_entries = max_entries

    def is_expired(self, entry: AuditEntry, now: datetime = None) -> bool:
        now = now or datetime.utcnow()
        cutoff = now - timedelta(days=self.max_age_days)
        return entry.timestamp < cutoff


def apply_retention(log: AuditLog, policy: RetentionPolicy, now: datetime = None) -> int:
    """Remove expired or excess entries. Returns number of entries removed."""
    now = now or datetime.utcnow()
    original = list(log.entries)

    # Remove by age
    kept = [e for e in original if not policy.is_expired(e, now)]

    # Trim to max_entries (keep most recent)
    if len(kept) > policy.max_entries:
        kept = kept[-policy.max_entries:]

    removed = len(original) - len(kept)
    log.entries = kept
    return removed


def retention_summary(log: AuditLog, policy: RetentionPolicy, now: datetime = None) -> dict:
    """Return a summary of what would be pruned without modifying the log."""
    now = now or datetime.utcnow()
    expired = sum(1 for e in log.entries if policy.is_expired(e, now))
    excess = max(0, len(log.entries) - policy.max_entries)
    return {
        "total": len(log.entries),
        "expired": expired,
        "excess": excess,
        "would_remove": min(len(log.entries), expired + excess),
    }
