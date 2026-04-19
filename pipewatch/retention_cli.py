"""CLI commands for managing audit log retention."""
import click
from pipewatch.audit_cli import get_audit_log
from pipewatch.retention import RetentionPolicy, apply_retention, retention_summary


@click.group()
def retention():
    """Manage audit log retention policies."""
    pass


@retention.command()
@click.option("--max-age-days", default=7, show_default=True, help="Max age of entries in days.")
@click.option("--max-entries", default=1000, show_default=True, help="Max number of entries to keep.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without removing entries.")
def prune(max_age_days, max_entries, dry_run):
    """Prune expired or excess audit log entries."""
    log = get_audit_log()
    try:
        policy = RetentionPolicy(max_age_days=max_age_days, max_entries=max_entries)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        summary = retention_summary(log, policy)
        click.echo(f"Total entries : {summary['total']}")
        click.echo(f"Expired       : {summary['expired']}")
        click.echo(f"Excess        : {summary['excess']}")
        click.echo(f"Would remove  : {summary['would_remove']}")
    else:
        removed = apply_retention(log, policy)
        click.echo(f"Removed {removed} entries. {len(log.entries)} remaining.")


@retention.command()
@click.option("--max-age-days", default=7, show_default=True)
@click.option("--max-entries", default=1000, show_default=True)
def preview(max_age_days, max_entries):
    """Preview retention impact without making changes."""
    log = get_audit_log()
    try:
        policy = RetentionPolicy(max_age_days=max_age_days, max_entries=max_entries)
    except ValueError as e:
        raise click.ClickException(str(e))
    summary = retention_summary(log, policy)
    for k, v in summary.items():
        click.echo(f"{k}: {v}")
