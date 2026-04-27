"""Export pipeline metrics to various formats."""
import json
import csv
import io
from typing import List
from pipewatch.metrics import PipelineMetric, to_dict


def to_json(metrics: List[PipelineMetric], indent: int = 2) -> str:
    """Serialize a list of metrics to a JSON string."""
    return json.dumps([to_dict(m) for m in metrics], indent=indent, default=str)


def to_csv(metrics: List[PipelineMetric]) -> str:
    """Serialize a list of metrics to CSV format."""
    if not metrics:
        return ""
    fieldnames = list(to_dict(metrics[0]).keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for m in metrics:
        writer.writerow(to_dict(m))
    return buf.getvalue()


def _prometheus_labels(m: PipelineMetric) -> str:
    """Build a Prometheus label string for a metric, including pipeline_id and status."""
    parts = [f'pipeline="{m.pipeline_id}"']
    if hasattr(m, 'status') and m.status is not None:
        parts.append(f'status="{m.status}"')
    return ",".join(parts)


def to_prometheus(metrics: List[PipelineMetric]) -> str:
    """Serialize metrics to Prometheus text exposition format."""
    lines = []
    lines.append("# HELP pipewatch_duration_seconds Pipeline run duration")
    lines.append("# TYPE pipewatch_duration_seconds gauge")
    for m in metrics:
        label = _prometheus_labels(m)
        lines.append(f"pipewatch_duration_seconds{{{label}}} {m.duration_seconds}")

    lines.append("# HELP pipewatch_error_count Pipeline error count")
    lines.append("# TYPE pipewatch_error_count gauge")
    for m in metrics:
        label = _prometheus_labels(m)
        lines.append(f"pipewatch_error_count{{{label}}} {m.error_count}")

    lines.append("# HELP pipewatch_rows_processed Rows processed by pipeline")
    lines.append("# TYPE pipewatch_rows_processed gauge")
    for m in metrics:
        label = _prometheus_labels(m)
        lines.append(f"pipewatch_rows_processed{{{label}}} {m.rows_processed}")

    return "\n".join(lines) + "\n"
