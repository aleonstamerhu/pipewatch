"""CLI commands for the pipewatch dashboard."""
import click
from pipewatch.collector import MetricsCollector
from pipewatch.alerts import AlertEngine, AlertRule
from pipewatch.reporter import Reporter
from pipewatch.dashboard import Dashboard

_collector = MetricsCollector()
_engine = AlertEngine(rules=[
    AlertRule(metric="error_rate", threshold=0.1, level="critical"),
    AlertRule(metric="duration_seconds", threshold=30.0, level="warning"),
])
_reporter = Reporter(collector=_collector, engine=_engine)
_dashboard = Dashboard(reporter=_reporter)


@click.group()
def dashboard():
    """Dashboard commands for pipeline health overview."""


@dashboard.command("show")
@click.argument("pipelines", nargs=-1)
@click.option("--all", "show_all", is_flag=True, help="Show all known pipelines.")
def show(pipelines, show_all):
    """Render a health dashboard for given pipelines."""
    if show_all:
        names = list(_collector._latest.keys())
    else:
        names = list(pipelines)
    if not names:
        click.echo("No pipelines specified. Use --all or provide pipeline names.")
        return
    click.echo(_dashboard.render(names))


@dashboard.command("summary")
@click.argument("pipeline")
def summary(pipeline):
    """Show a single pipeline summary."""
    report = _reporter.report(pipeline)
    click.echo(f"Pipeline : {pipeline}")
    click.echo(f"Status   : {report.status}")
    click.echo(f"Summary  : {report.summary}")
    if report.alerts:
        click.echo("Alerts:")
        for alert in report.alerts:
            click.echo(f"  - {alert}")
    else:
        click.echo("Alerts   : none")
