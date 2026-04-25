"""CLI commands for metric aggregation."""

from __future__ import annotations

import click

from pipewatch.collector import MetricsCollector
from pipewatch.aggregation import aggregate_pipeline, aggregate_all

_collector: MetricsCollector | None = None


def _get_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


@click.group()
def aggregation() -> None:
    """Aggregate historical pipeline metrics."""


@aggregation.command("show")
@click.argument("pipeline")
def show(pipeline: str) -> None:
    """Show aggregated stats for a single PIPELINE."""
    collector = _get_collector()
    history = collector.history(pipeline)
    if not history:
        click.echo(f"No data for pipeline '{pipeline}'.")
        return
    result = aggregate_pipeline(history)
    if result is None:
        click.echo(f"Could not aggregate data for '{pipeline}'.")
        return
    click.echo(f"Pipeline:       {result.pipeline}")
    click.echo(f"Samples:        {result.sample_count}")
    click.echo(f"Avg duration:   {result.avg_duration:.2f}s" if result.avg_duration is not None else "Avg duration:   n/a")
    click.echo(f"Min duration:   {result.min_duration:.2f}s" if result.min_duration is not None else "Min duration:   n/a")
    click.echo(f"Max duration:   {result.max_duration:.2f}s" if result.max_duration is not None else "Max duration:   n/a")
    click.echo(f"Avg error rate: {result.avg_error_rate:.4f}" if result.avg_error_rate is not None else "Avg error rate: n/a")
    click.echo(f"Max error rate: {result.max_error_rate:.4f}" if result.max_error_rate is not None else "Max error rate: n/a")
    click.echo(f"Dominant status:{result.dominant_status.value}")


@aggregation.command("all")
def all_aggregations() -> None:
    """Show aggregated stats for all known pipelines."""
    collector = _get_collector()
    results = aggregate_all(collector)
    if not results:
        click.echo("No pipeline data available.")
        return
    for result in results.values():
        click.echo(result.summary())
