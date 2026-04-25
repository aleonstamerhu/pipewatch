"""CLI commands for pipeline similarity detection."""

import click
from pipewatch.collector import MetricsCollector
from pipewatch.similarity import compute_similarity, find_similar_pipelines

_collector: MetricsCollector = MetricsCollector()


def _get_collector() -> MetricsCollector:
    return _collector


@click.group()
def similarity():
    """Pipeline similarity detection commands."""
    pass


@similarity.command("pair")
@click.argument("pipeline_a")
@click.argument("pipeline_b")
@click.option("--min-samples", default=3, show_default=True, help="Minimum history samples required.")
def pair(pipeline_a: str, pipeline_b: str, min_samples: int):
    """Compute similarity between two specific pipelines."""
    collector = _get_collector()
    result = compute_similarity(collector, pipeline_a, pipeline_b, min_samples=min_samples)
    if result is None:
        click.echo(
            f"Not enough data to compare '{pipeline_a}' and '{pipeline_b}' "
            f"(need at least {min_samples} samples each)."
        )
        return
    click.echo(result.summary())


@similarity.command("find")
@click.argument("pipeline")
@click.option("--threshold", default=0.7, show_default=True, help="Minimum similarity score (0.0-1.0).")
@click.option("--min-samples", default=3, show_default=True, help="Minimum history samples required.")
def find(pipeline: str, threshold: float, min_samples: int):
    """Find all pipelines similar to the given pipeline."""
    collector = _get_collector()
    results = find_similar_pipelines(
        collector, pipeline, threshold=threshold, min_samples=min_samples
    )
    if not results:
        click.echo(f"No pipelines similar to '{pipeline}' found above threshold {threshold}.")
        return
    for r in results:
        click.echo(r.summary())
