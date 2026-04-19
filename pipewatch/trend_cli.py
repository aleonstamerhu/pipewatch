"""CLI commands for pipeline trend analysis."""
import click
from pipewatch.collector import MetricsCollector
from pipewatch.trend import analyze_trend, analyze_all

_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    return _collector


@click.group()
def trend():
    """Trend analysis commands."""


@trend.command("show")
@click.argument("pipeline")
def show(pipeline: str):
    """Show trend for a specific pipeline."""
    collector = get_collector()
    history = collector.history(pipeline)
    result = analyze_trend(pipeline, history)
    if result is None:
        click.echo(f"No data for pipeline: {pipeline}")
        return
    click.echo(result.summary())


@trend.command("all")
def all_trends():
    """Show trends for all pipelines."""
    collector = get_collector()
    results = analyze_all(collector)
    if not results:
        click.echo("No pipeline data available.")
        return
    for r in results:
        click.echo(r.summary())


@trend.command("direction")
@click.argument("pipeline")
def direction(pipeline: str):
    """Print only the trend direction for a pipeline."""
    collector = get_collector()
    history = collector.history(pipeline)
    result = analyze_trend(pipeline, history)
    if result is None:
        click.echo("unknown")
    else:
        click.echo(result.direction)
