"""CLI commands for managing pipeline labels."""

from __future__ import annotations

import click

from pipewatch.labeling import LabelStore

_store: LabelStore = LabelStore()


def _get_store() -> LabelStore:
    return _store


@click.group()
def labeling() -> None:
    """Manage key-value labels on pipelines."""


@labeling.command("set")
@click.argument("pipeline")
@click.argument("key")
@click.argument("value")
def set_label(pipeline: str, key: str, value: str) -> None:
    """Set a label KEY=VALUE on PIPELINE."""
    store = _get_store()
    store.set(pipeline, key, value)
    click.echo(f"Set '{key}={value}' on pipeline '{pipeline}'.")


@labeling.command("get")
@click.argument("pipeline")
@click.argument("key")
def get_label(pipeline: str, key: str) -> None:
    """Get the value of label KEY on PIPELINE."""
    store = _get_store()
    value = store.get(pipeline, key)
    if value is None:
        click.echo(f"Label '{key}' not found on pipeline '{pipeline}'.")
    else:
        click.echo(f"{key}={value}")


@labeling.command("remove")
@click.argument("pipeline")
@click.argument("key")
def remove_label(pipeline: str, key: str) -> None:
    """Remove label KEY from PIPELINE."""
    store = _get_store()
    removed = store.remove(pipeline, key)
    if removed:
        click.echo(f"Removed label '{key}' from pipeline '{pipeline}'.")
    else:
        click.echo(f"Label '{key}' was not set on pipeline '{pipeline}'.")


@labeling.command("list")
@click.argument("pipeline")
def list_labels(pipeline: str) -> None:
    """List all labels for PIPELINE."""
    store = _get_store()
    labels = store.get_all(pipeline)
    if not labels:
        click.echo(f"No labels set for pipeline '{pipeline}'.")
        return
    for key, value in sorted(labels.items()):
        click.echo(f"  {key}={value}")


@labeling.command("find")
@click.argument("key")
@click.option("--value", default=None, help="Filter by label value.")
def find_pipelines(key: str, value: str) -> None:
    """Find pipelines that have label KEY (optionally matching VALUE)."""
    store = _get_store()
    pipelines = store.pipelines_with_label(key, value)
    if not pipelines:
        click.echo("No pipelines found.")
        return
    for p in pipelines:
        click.echo(f"  {p}")
