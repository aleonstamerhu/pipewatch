"""CLI commands for pipeline metric snapshots."""
import click
from pipewatch.collector import MetricsCollector
from pipewatch.snapshot import save_snapshot, load_snapshot, snapshot_summary

_collector = MetricsCollector()


@click.group()
def snapshot():
    """Save and restore pipeline metric snapshots."""


@snapshot.command("save")
@click.argument("path")
def save_cmd(path: str):
    """Save current latest metrics to PATH."""
    pipelines = _collector.list_pipelines()
    if not pipelines:
        click.echo("No pipeline data to snapshot.")
        return
    metrics = [_collector.latest(p) for p in pipelines if _collector.latest(p)]
    save_snapshot(metrics, path)
    click.echo(f"Snapshot saved: {len(metrics)} pipeline(s) → {path}")


@snapshot.command("load")
@click.argument("path")
def load_cmd(path: str):
    """Load metrics from a snapshot at PATH and display summary."""
    try:
        metrics = load_snapshot(path)
    except FileNotFoundError:
        click.echo(f"File not found: {path}", err=True)
        raise SystemExit(1)
    summary = snapshot_summary(metrics)
    click.echo(f"Loaded {summary['total']} metric(s) from {path}")
    for status, count in summary["by_status"].items():
        click.echo(f"  {status}: {count}")


@snapshot.command("summary")
@click.argument("path")
def summary_cmd(path: str):
    """Print a status breakdown for snapshot at PATH."""
    try:
        metrics = load_snapshot(path)
    except FileNotFoundError:
        click.echo(f"File not found: {path}", err=True)
        raise SystemExit(1)
    info = snapshot_summary(metrics)
    click.echo(f"Total pipelines: {info['total']}")
    for status, count in info["by_status"].items():
        click.echo(f"  {status}: {count}")
