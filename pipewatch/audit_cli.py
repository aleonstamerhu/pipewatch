"""CLI commands for viewing the pipeline audit log."""

import click
from pipewatch.audit import AuditLog

_audit_log = AuditLog()


def get_audit_log() -> AuditLog:
    return _audit_log


@click.group()
def audit():
    """View pipeline audit log."""


@audit.command("show")
@click.option("--pipeline", default=None, help="Filter by pipeline name.")
@click.option("--limit", default=20, show_default=True, help="Max entries to show.")
def show(pipeline, limit):
    """Show recent audit log entries."""
    log = get_audit_log()
    entries = log.entries(pipeline=pipeline)
    if not entries:
        click.echo("No audit entries found.")
        return
    for entry in entries[-limit:]:
        click.echo(
            f"[{entry.timestamp.isoformat()}] "
            f"{entry.pipeline} | {entry.event_type.upper()} | "
            f"{entry.status} | {entry.detail}"
        )


@audit.command("clear")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def clear(yes):
    """Clear all audit log entries."""
    if not yes:
        click.confirm("Clear all audit entries?", abort=True)
    get_audit_log().clear()
    click.echo("Audit log cleared.")


@audit.command("count")
@click.option("--pipeline", default=None, help="Filter by pipeline name.")
def count(pipeline):
    """Count audit log entries."""
    log = get_audit_log()
    n = len(log.entries(pipeline=pipeline))
    label = f"for '{pipeline}'" if pipeline else "total"
    click.echo(f"Audit entries {label}: {n}")
