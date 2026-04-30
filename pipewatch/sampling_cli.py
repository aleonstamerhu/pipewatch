"""CLI commands for inspecting metric sampling behaviour."""
from __future__ import annotations

import click

from pipewatch.collector import MetricsCollector
from pipewatch.sampling import SamplingPolicy, sample_all, sample_pipeline

_collector: MetricsCollector = MetricsCollector()


def _get_collector() -> MetricsCollector:
    return _collector


@click.group()
def sampling() -> None:
    """Metric sampling utilities."""


@sampling.command("show")
@click.argument("pipeline")
@click.option("--max-samples", default=50, show_default=True, help="Max samples to keep.")
@click.option(
    "--min-interval",
    default=0.0,
    show_default=True,
    help="Minimum seconds between samples.",
)
def show(pipeline: str, max_samples: int, min_interval: float) -> None:
    """Show sampling result for a single PIPELINE."""
    collector = _get_collector()
    history = collector.history(pipeline)
    if not history:
        click.echo(f"No data for pipeline '{pipeline}'.")
        return
    policy = SamplingPolicy(max_samples=max_samples, min_interval_seconds=min_interval)
    result = sample_pipeline(pipeline, history, policy)
    if result is None:
        click.echo(f"No samples produced for '{pipeline}'.")
        return
    click.echo(result.summary())


@sampling.command("all")
@click.option("--max-samples", default=50, show_default=True)
@click.option("--min-interval", default=0.0, show_default=True)
def all_sampling(max_samples: int, min_interval: float) -> None:
    """Show sampling results for all tracked pipelines."""
    collector = _get_collector()
    policy = SamplingPolicy(max_samples=max_samples, min_interval_seconds=min_interval)
    results = sample_all(collector, policy)
    if not results:
        click.echo("No pipelines found.")
        return
    for r in results:
        click.echo(r.summary())
