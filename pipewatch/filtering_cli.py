"""CLI commands for filtering pipeline metrics."""

import click
from pipewatch.collector import MetricsCollector
from pipewatch.metrics import MetricStatus
from pipewatch.filtering import FilterCriteria, filter_metrics, filter_summary
from pipewatch.tagging import TagStore

_collector: MetricsCollector = MetricsCollector()
_tag_store: TagStore = TagStore()


def _get_collector() -> MetricsCollector:
    return _collector


def _get_tag_store() -> TagStore:
    return _tag_store


@click.group()
def filtering():
    """Filter pipeline metrics by status, error rate, duration, or tags."""


@filtering.command("query")
@click.option("--status", "statuses", multiple=True, help="Filter by status (ok, warning, critical, unknown).")
@click.option("--min-error-rate", type=float, default=None)
@click.option("--max-error-rate", type=float, default=None)
@click.option("--min-duration", type=float, default=None)
@click.option("--max-duration", type=float, default=None)
@click.option("--name-contains", default=None)
@click.option("--tag", "tags", multiple=True)
def query(statuses, min_error_rate, max_error_rate, min_duration, max_duration, name_contains, tags):
    """Query latest metrics using filter criteria."""
    collector = _get_collector()
    tag_store = _get_tag_store()

    all_metrics = [m for name in collector.pipelines() if (m := collector.latest(name)) is not None]

    parsed_statuses = []
    for s in statuses:
        try:
            parsed_statuses.append(MetricStatus(s))
        except ValueError:
            click.echo(f"Unknown status: {s}", err=True)
            raise SystemExit(1)

    criteria = FilterCriteria(
        statuses=parsed_statuses or None,
        min_error_rate=min_error_rate,
        max_error_rate=max_error_rate,
        min_duration=min_duration,
        max_duration=max_duration,
        name_contains=name_contains,
        tags=list(tags) or None,
    )

    tag_map = {name: list(tag_store.get(name)) for name in collector.pipelines()}
    results = filter_metrics(all_metrics, criteria, tag_map)

    if not results:
        click.echo("No pipelines match the given criteria.")
        return

    for m in results:
        click.echo(f"{m.pipeline_name:30s}  status={m.status.value}  errors={m.error_rate:.2f}  duration={m.duration_seconds:.1f}s")

    totals = filter_summary(results)
    click.echo(f"\nMatched {totals['total']} pipeline(s).")
