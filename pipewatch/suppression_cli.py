"""CLI commands for managing alert suppression rules."""
from __future__ import annotations

from typing import Optional

import click

from pipewatch.suppression import SuppressionStore, make_suppression_rule

_store = SuppressionStore()


def _get_store() -> SuppressionStore:
    return _store


@click.group()
def suppression() -> None:
    """Manage alert suppression rules."""


@suppression.command("add")
@click.argument("pipeline")
@click.option("--severity", default=None, help="Severity to suppress (omit for all).")
@click.option("--minutes", default=None, type=int, help="Duration in minutes (omit for permanent).")
@click.option("--reason", default="", help="Reason for suppression.")
def add_rule(pipeline: str, severity: Optional[str], minutes: Optional[int], reason: str) -> None:
    """Add a suppression rule for PIPELINE."""
    store = _get_store()
    rule = make_suppression_rule(pipeline, severity=severity, duration_minutes=minutes, reason=reason)
    store.add(rule)
    duration_label = f"{minutes}m" if minutes else "permanent"
    severity_label = severity or "all severities"
    click.echo(f"Suppressed '{pipeline}' [{severity_label}] for {duration_label}.")
    if reason:
        click.echo(f"Reason: {reason}")


@suppression.command("remove")
@click.argument("pipeline")
@click.option("--severity", default=None)
def remove_rule(pipeline: str, severity: Optional[str]) -> None:
    """Remove suppression rule for PIPELINE."""
    store = _get_store()
    removed = store.remove(pipeline, severity=severity)
    if removed:
        click.echo(f"Removed {removed} suppression rule(s) for '{pipeline}'.")
    else:
        click.echo(f"No matching rules found for '{pipeline}'.")


@suppression.command("list")
def list_rules() -> None:
    """List all active suppression rules."""
    store = _get_store()
    rules = store.active_rules()
    if not rules:
        click.echo("No active suppression rules.")
        return
    for r in rules:
        exp = r.expires_at.isoformat() if r.expires_at else "never"
        sev = r.severity or "all"
        click.echo(f"  {r.pipeline} | severity={sev} | expires={exp} | reason={r.reason or '-'}")


@suppression.command("purge")
def purge_expired() -> None:
    """Remove all expired suppression rules."""
    store = _get_store()
    removed = store.purge_expired()
    click.echo(f"Purged {removed} expired rule(s).")
