"""CLI commands for managing the pipewatch scheduler."""

import click
from pipewatch.scheduler import Scheduler
from pipewatch.schedule_config import load_from_yaml
from pipewatch.collector import MetricsCollector
from pipewatch.alerts import AlertEngine, AlertRule
from pipewatch.metrics import MetricStatus

_scheduler = Scheduler()
_collector = MetricsCollector()
_engine = AlertEngine(rules=[
    AlertRule(name="errors", field="error_count", threshold=0, level="CRITICAL"),
])


def _check_pipeline(pipeline_name: str) -> None:
    metric = _collector.latest(pipeline_name)
    if metric:
        alerts = _engine.evaluate(metric)
        for alert in alerts:
            click.echo(f"[ALERT] {alert}")


@click.group()
def schedule():
    """Manage scheduled pipeline checks."""


@schedule.command("load")
@click.argument("config_path")
def load_config(config_path: str):
    """Load scheduled jobs from a YAML config file."""
    try:
        configs = load_from_yaml(config_path)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        raise SystemExit(1)

    for cfg in configs:
        _scheduler.add_job(cfg.pipeline_name, cfg.interval_seconds, _check_pipeline)
        click.echo(f"Scheduled '{cfg.pipeline_name}' every {cfg.interval_seconds}s")


@schedule.command("list")
def list_jobs():
    """List all scheduled pipeline jobs."""
    jobs = _scheduler.list_jobs()
    if not jobs:
        click.echo("No scheduled jobs.")
    for name in jobs:
        click.echo(f"  - {name}")


@schedule.command("remove")
@click.argument("pipeline_name")
def remove_job(pipeline_name: str):
    """Remove a scheduled job by pipeline name."""
    removed = _scheduler.remove_job(pipeline_name)
    if removed:
        click.echo(f"Removed job for '{pipeline_name}'.")
    else:
        click.echo(f"No job found for '{pipeline_name}'.")
