"""CLI commands for pipeline grouping by tag."""

import click
from pipewatch.tagging import TagStore
from pipewatch.collector import MetricsCollector
from pipewatch.grouping import group_by_tag, group_all

_tag_store: TagStore = TagStore()
_collector: MetricsCollector = MetricsCollector()


def _get_store() -> TagStore:
    return _tag_store


def _get_collector() -> MetricsCollector:
    return _collector


@click.group()
def grouping():
    """Commands for grouped pipeline health views."""
    pass


@grouping.command("show")
@click.argument("tag")
def show(tag: str):
    """Show health summary for all pipelines with TAG."""
    store = _get_store()
    collector = _get_collector()
    result = group_by_tag(tag, store, collector)
    if result is None:
        click.echo(f"No pipelines found with tag '{tag}'.")
        return
    click.echo(result.summary())
    for pipeline in result.pipelines:
        metric = collector.latest(pipeline)
        status = metric.status.value if metric else "unknown"
        click.echo(f"  - {pipeline}: {status}")


@grouping.command("all")
def all_groups():
    """Show health summaries for all tags."""
    store = _get_store()
    collector = _get_collector()
    summaries = group_all(store, collector)
    if not summaries:
        click.echo("No tagged pipelines found.")
        return
    for s in summaries:
        click.echo(s.summary())


@grouping.command("dominant")
@click.argument("tag")
def dominant(tag: str):
    """Print the dominant status for pipelines with TAG."""
    store = _get_store()
    collector = _get_collector()
    result = group_by_tag(tag, store, collector)
    if result is None:
        click.echo(f"No pipelines found with tag '{tag}'.")
        return
    click.echo(result.dominant_status().value)
