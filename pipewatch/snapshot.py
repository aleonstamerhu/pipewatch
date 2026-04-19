"""Snapshot: capture and restore pipeline metric state."""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any
from pipewatch.metrics import PipelineMetric, MetricStatus


def _metric_to_dict(m: PipelineMetric) -> dict[str, Any]:
    return {
        "pipeline": m.pipeline,
        "duration": m.duration,
        "error_count": m.error_count,
        "rows_processed": m.rows_processed,
        "status": m.status.value,
        "timestamp": m.timestamp.isoformat(),
    }


def _metric_from_dict(d: dict[str, Any]) -> PipelineMetric:
    m = PipelineMetric(
        pipeline=d["pipeline"],
        duration=d["duration"],
        error_count=d["error_count"],
        rows_processed=d["rows_processed"],
    )
    m.status = MetricStatus(d["status"])
    m.timestamp = datetime.fromisoformat(d["timestamp"])
    return m


def save_snapshot(metrics: list[PipelineMetric], path: str) -> None:
    """Serialize a list of metrics to a JSON snapshot file."""
    payload = {
        "saved_at": datetime.utcnow().isoformat(),
        "metrics": [_metric_to_dict(m) for m in metrics],
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def load_snapshot(path: str) -> list[PipelineMetric]:
    """Deserialize metrics from a JSON snapshot file."""
    with open(path) as f:
        payload = json.load(f)
    return [_metric_from_dict(d) for d in payload["metrics"]]


def snapshot_summary(metrics: list[PipelineMetric]) -> dict[str, Any]:
    """Return a brief summary dict for a snapshot."""
    status_counts: dict[str, int] = {}
    for m in metrics:
        key = m.status.value
        status_counts[key] = status_counts.get(key, 0) + 1
    return {"total": len(metrics), "by_status": status_counts}
