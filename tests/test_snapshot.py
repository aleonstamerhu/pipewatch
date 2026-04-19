"""Tests for pipewatch.snapshot."""
import json
import pytest
from datetime import datetime
from pipewatch.metrics import PipelineMetric, MetricStatus, compute_status
from pipewatch.snapshot import save_snapshot, load_snapshot, snapshot_summary


def make_metric(pipeline="pipe", duration=1.0, error_count=0, rows=100):
    m = PipelineMetric(pipeline=pipeline, duration=duration,
                       error_count=error_count, rows_processed=rows)
    m.status = compute_status(m)
    return m


def test_save_creates_file(tmp_path):
    path = str(tmp_path / "snap.json")
    metrics = [make_metric("a"), make_metric("b")]
    save_snapshot(metrics, path)
    with open(path) as f:
        data = json.load(f)
    assert "saved_at" in data
    assert len(data["metrics"]) == 2


def test_roundtrip_preserves_fields(tmp_path):
    path = str(tmp_path / "snap.json")
    m = make_metric("etl", duration=3.5, error_count=0, rows=42)
    save_snapshot([m], path)
    restored = load_snapshot(path)
    assert len(restored) == 1
    r = restored[0]
    assert r.pipeline == "etl"
    assert r.duration == 3.5
    assert r.rows_processed == 42
    assert r.status == m.status


def test_roundtrip_critical(tmp_path):
    path = str(tmp_path / "snap.json")
    m = make_metric("bad", error_count=5)
    save_snapshot([m], path)
    restored = load_snapshot(path)
    assert restored[0].status == MetricStatus.CRITICAL


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_snapshot("/nonexistent/path/snap.json")


def test_snapshot_summary_counts():
    metrics = [
        make_metric("a"),
        make_metric("b"),
        make_metric("c", error_count=5),
    ]
    summary = snapshot_summary(metrics)
    assert summary["total"] == 3
    assert summary["by_status"].get(MetricStatus.CRITICAL.value, 0) >= 1


def test_snapshot_summary_empty():
    summary = snapshot_summary([])
    assert summary["total"] == 0
    assert summary["by_status"] == {}
