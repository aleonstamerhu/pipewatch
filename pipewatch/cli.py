"""CLI entry point for pipewatch."""
import click
from pipewatch.collector import MetricsCollector
from pipewatch.alerts import AlertEngine, AlertRule
from pipewatch.reporter import Reporter
from pipewatch.metrics import MetricStatus


_collector = MetricsCollector(max_history=100)
_engine = AlertEngine(rules=[
    AlertRule(metric="error_count", threshold=1, level="critical"),
    AlertRule(metric="duration_seconds", threshold=60, level="warning"),
])
_reporter = Reporter(collector=_collector, engine=_engine)


@click.group()
def cli():
    """pipewatch — monitor and alert on ETL pipeline health."""
    pass


@cli.command()
@click.argument("pipeline")
@click.option("--duration", default=0.0, type=float, help="Run duration in seconds.")
@click.option("--errors", default=0, type=int, help="Number of errors.")
@click.option("--rows", default=0, type=int, help="Rows processed.")
def record(pipeline, duration, errors, rows):
    """Record a metric snapshot for a pipeline."""
    metric = _collector.record(
        pipeline_id=pipeline,
        duration_seconds=duration,
        error_count=errors,
        rows_processed=rows,
    )
    click.echo(f"Recorded [{metric.status.value}] for '{pipeline}'")
    alerts = _engine.evaluate(metric)
    for alert in alerts:
        click.secho(f"  ALERT: {alert}", fg="red" if alert.level == "critical" else "yellow")


@cli.command()
@click.argument("pipeline")
def status(pipeline):
    """Show the latest status for a pipeline."""
    report = _reporter.report(pipeline)
    color = {"ok": "green", "warning": "yellow", "critical": "red"}.get(report.status, "white")
    click.secho(f"{pipeline}: {report.status.upper()} — {report.summary}", fg=color)


@cli.command(name="list")
def list_pipelines():
    """List all tracked pipelines."""
    pipelines = _collector.pipelines()
    if not pipelines:
        click.echo("No pipelines tracked yet.")
        return
    for pid in pipelines:
        report = _reporter.report(pid)
        click.echo(f"  {pid}: {report.status}")


if __name__ == "__main__":
    cli()
