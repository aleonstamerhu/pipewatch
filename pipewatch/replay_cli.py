"""CLI commands for replaying historical metrics."""

import click
from pipewatch.alerts import AlertEngine, AlertRule
from pipewatch.audit import AuditLog
from pipewatch.collector import MetricsCollector
from pipewatch.replay import replay_pipeline, replay_from_audit

_audit_log: AuditLog = AuditLog()
_collector: MetricsCollector = MetricsCollector()
_engine: AlertEngine = AlertEngine(rules=[
    AlertRule(name="high_errors", error_rate_threshold=0.05, severity="critical"),
    AlertRule(name="slow_pipeline", duration_threshold=300.0, severity="warning"),
])


def _get_audit_log() -> AuditLog:
    return _audit_log


def _get_collector() -> MetricsCollector:
    return _collector


def _get_engine() -> AlertEngine:
    return _engine


@click.group()
def replay():
    """Replay historical metrics through the alert engine."""


@replay.command("run")
@click.argument("pipeline")
@click.option("--source", default="collector", type=click.Choice(["collector", "audit"]),
              show_default=True, help="Data source for replay.")
def run_cmd(pipeline: str, source: str):
    """Replay metrics for PIPELINE and report alerts fired."""
    engine = _get_engine()

    if source == "audit":
        log = _get_audit_log()
        result = replay_from_audit(pipeline, log, engine)
    else:
        collector = _get_collector()
        metrics = collector.history(pipeline)
        from pipewatch.replay import replay_pipeline
        result = replay_pipeline(pipeline, metrics, engine)

    click.echo(result.summary())
    if result.alerts_fired:
        click.echo(f"  Alerts:")
        for alert in result.alerts_fired:
            click.echo(f"    [{alert.severity.upper()}] {alert.rule_name} — {alert.message}")
    else:
        click.echo("  No alerts fired.")


@replay.command("summary")
@click.argument("pipeline")
def summary_cmd(pipeline: str):
    """Print a one-line replay summary for PIPELINE using collector history."""
    collector = _get_collector()
    engine = _get_engine()
    metrics = collector.history(pipeline)
    from pipewatch.replay import replay_pipeline
    result = replay_pipeline(pipeline, metrics, engine)
    click.echo(result.summary())
