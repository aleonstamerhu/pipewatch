"""Tests for pipewatch.exporter."""
import json
import pytest
from datetime import datetime
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.exporter import to_json, to_csv, to_prometheus


def make_metric(pipeline_id="pipe1", duration=10.0, errors=0, rows=100):
    return PipelineMetric(
        pipeline_id=pipeline_id,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        duration_seconds=duration,
        error_count=errors,
        rows_processed=rows,
        status=MetricStatus.OK,
    )


def test_to_json_returns_list():
    metrics = [make_metric(), make_metric(pipeline_id="pipe2")]
    result = json.loads(to_json(metrics))
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["pipeline_id"] == "pipe1"


def test_to_json_empty():
    assert to_json([]) == "[]"


def test_to_csv_contains_header():
    metrics = [make_metric()]
    result = to_csv(metrics)
    assert "pipeline_id" in result
    assert "pipe1" in result


def test_to_csv_empty():
    assert to_csv([]) == ""


def test_to_csv_multiple_rows():
    metrics = [make_metric("a"), make_metric("b")]
    result = to_csv(metrics)
    lines = result.strip().splitlines()
    assert len(lines) == 3  # header + 2 rows


def test_to_prometheus_contains_metrics():
    metrics = [make_metric(duration=5.5, errors=2, rows=42)]
    result = to_prometheus(metrics)
    assert 'pipewatch_duration_seconds{pipeline="pipe1"} 5.5' in result
    assert 'pipewatch_error_count{pipeline="pipe1"} 2' in result
    assert 'pipewatch_rows_processed{pipeline="pipe1"} 42' in result


def test_to_prometheus_help_lines():
    result = to_prometheus([make_metric()])
    assert "# HELP" in result
    assert "# TYPE" in result
