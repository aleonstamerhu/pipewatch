"""CLI commands for inspecting alert routing rules."""

from __future__ import annotations

from typing import List

import click

from pipewatch.routing import AlertRouter, RoutingRule
from pipewatch.notifier import ConsoleNotifier
from pipewatch.tagging import TagStore

# ---------------------------------------------------------------------------
# Shared state (in a real app these would be injected / loaded from config)
# ---------------------------------------------------------------------------

_router: AlertRouter = AlertRouter(fallback=[ConsoleNotifier()])
_tag_store: TagStore = TagStore()


def _get_router() -> AlertRouter:
    return _router


def _get_tag_store() -> TagStore:
    return _tag_store


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def routing() -> None:
    """Manage alert routing rules."""


@routing.command("list")
def list_rules() -> None:
    """List all routing rules."""
    router = _get_router()
    if not router.rules:
        click.echo("No routing rules defined.")
        return
    for i, rule in enumerate(router.rules, start=1):
        tag_part = f"tag={rule.tag}" if rule.tag else "any tag"
        sev_part = f"severity={rule.severity}" if rule.severity else "any severity"
        notifier_names = ", ".join(type(n).__name__ for n in rule.notifiers)
        click.echo(f"[{i}] {tag_part} | {sev_part} -> {notifier_names}")


@routing.command("add")
@click.option("--tag", default=None, help="Match pipelines with this tag.")
@click.option(
    "--severity",
    default=None,
    type=click.Choice(["warning", "critical"]),
    help="Match alerts of this severity.",
)
def add_rule(tag: str, severity: str) -> None:
    """Add a console-notifier routing rule (demo)."""
    if tag is None and severity is None:
        raise click.UsageError("Provide at least --tag or --severity.")
    rule = RoutingRule(notifiers=[ConsoleNotifier()], tag=tag, severity=severity)
    _get_router().add_rule(rule)
    click.echo("Routing rule added.")


@routing.command("clear")
def clear_rules() -> None:
    """Remove all routing rules."""
    router = _get_router()
    router.rules.clear()
    click.echo("All routing rules cleared.")
