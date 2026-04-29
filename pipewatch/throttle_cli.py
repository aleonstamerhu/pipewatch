"""CLI commands for inspecting and managing alert throttle state."""

from __future__ import annotations

from datetime import datetime

import click

from pipewatch.throttle import AlertThrottler, ThrottlePolicy

# Module-level singleton so commands share state within a process.
_throttler: AlertThrottler = AlertThrottler()


def _get_throttler() -> AlertThrottler:
    return _throttler


@click.group(name="throttle")
def throttle() -> None:
    """Manage alert throttle state."""


@throttle.command(name="status")
def status() -> None:
    """Show current throttle state (keys and last-sent timestamps)."""
    t = _get_throttler()
    entries = t.state._last_sent
    if not entries:
        click.echo("No throttle state recorded.")
        return
    click.echo(f"{'Key':<45} {'Last Sent (UTC)':<25} {'Cooldown (s)'}")
    click.echo("-" * 80)
    for key, ts in sorted(entries.items()):
        click.echo(f"{key:<45} {ts.strftime('%Y-%m-%d %H:%M:%S'):<25} {t.policy.cooldown_seconds}")


@throttle.command(name="reset")
@click.argument("pipeline")
@click.argument("rule_name")
def reset(pipeline: str, rule_name: str) -> None:
    """Reset throttle state for PIPELINE / RULE_NAME pair."""
    t = _get_throttler()
    t.state.reset(pipeline, rule_name)
    click.echo(f"Throttle state cleared for '{pipeline}' / '{rule_name}'.")


@throttle.command(name="clear")
def clear() -> None:
    """Clear ALL throttle state."""
    t = _get_throttler()
    t.state.clear()
    click.echo("All throttle state cleared.")


@throttle.command(name="set-cooldown")
@click.argument("seconds", type=int)
def set_cooldown(seconds: int) -> None:
    """Update the cooldown window to SECONDS."""
    t = _get_throttler()
    t.policy = ThrottlePolicy(cooldown_seconds=seconds)
    click.echo(f"Cooldown updated to {seconds} second(s).")
