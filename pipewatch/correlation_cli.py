"""CLI commands for pipeline correlation analysis."""
import click
from typing import Optional

from pipewatch.collector import MetricsCollector
from pipewatch.correlation import correlate_all, correlate_pipelines

_collector: Optional[MetricsCollector] = None


def _get_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


@click.group()
def correlation() -> None:
    """Correlation analysis between pipeline metrics."""


@correlation.command("all")
def all_correlations() -> None:
    """Show pairwise correlations for all tracked pipelines."""
    collector = _get_collector()
    pipelines = collector.list_pipelines()
    if len(pipelines) < 2:
        click.echo("Need at least 2 pipelines to compute correlations.")
        return
    histories = {p: collector.history(p) for p in pipelines}
    results = correlate_all(histories)
    if not results:
        click.echo("Not enough data to compute correlations.")
        return
    for r in results:
        click.echo(r.summary())


@correlation.command("pair")
@click.argument("pipeline_a")
@click.argument("pipeline_b")
def pair(pipeline_a: str, pipeline_b: str) -> None:
    """Show correlation between two specific pipelines."""
    collector = _get_collector()
    hist_a = collector.history(pipeline_a)
    hist_b = collector.history(pipeline_b)
    if not hist_a:
        click.echo(f"No data for pipeline: {pipeline_a}")
        return
    if not hist_b:
        click.echo(f"No data for pipeline: {pipeline_b}")
        return
    result = correlate_pipelines(hist_a, hist_b, pipeline_a, pipeline_b)
    if result is None:
        click.echo("Not enough data to compute correlation (need at least 2 samples each).")
        return
    click.echo(result.summary())
