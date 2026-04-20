"""CLI commands for baseline management."""

from __future__ import annotations

import click

from pipewatch.baseline import BaselineStore
from pipewatch.collector import MetricsCollector

_store = BaselineStore()
_collector = MetricsCollector()


def _get_store() -> BaselineStore:
    return _store


def _get_collector() -> MetricsCollector:
    return _collector


@click.group()
def baseline() -> None:
    """Manage pipeline metric baselines."""


@baseline.command("compute")
@click.argument("pipeline")
@click.option("--samples", default=10, show_default=True, help="Number of recent samples to use.")
def compute(pipeline: str, samples: int) -> None:
    """Compute and store a baseline for PIPELINE."""
    collector = _get_collector()
    store = _get_store()
    history = collector.history(pipeline, limit=samples)
    if not history:
        click.echo(f"No data found for pipeline '{pipeline}'.")
        raise SystemExit(1)
    entry = store.compute_and_store(pipeline, history)
    click.echo(
        f"Baseline stored for '{pipeline}': "
        f"avg_duration={entry.avg_duration:.2f}s, "
        f"avg_error_rate={entry.avg_error_rate:.2f}, "
        f"samples={entry.sample_count}"
    )


@baseline.command("compare")
@click.argument("pipeline")
def compare(pipeline: str) -> None:
    """Compare the latest metric for PIPELINE against its baseline."""
    collector = _get_collector()
    store = _get_store()
    metric = collector.latest(pipeline)
    if metric is None:
        click.echo(f"No recent metric found for pipeline '{pipeline}'.")
        raise SystemExit(1)
    result = store.compare(metric)
    click.echo(result.summary())


@baseline.command("list")
def list_baselines() -> None:
    """List all pipelines with stored baselines."""
    store = _get_store()
    pipelines = store.all_pipelines()
    if not pipelines:
        click.echo("No baselines stored.")
        return
    for name in pipelines:
        entry = store.get(name)
        click.echo(
            f"{name}: avg_duration={entry.avg_duration:.2f}s, "
            f"avg_error_rate={entry.avg_error_rate:.2f}, "
            f"samples={entry.sample_count}, recorded_at={entry.recorded_at}"
        )
