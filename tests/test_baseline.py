"""Tests for pipewatch.baseline module."""

from __future__ import annotations

from datetime import datetime

import pytest

from pipewatch.baseline import BaselineEntry, BaselineStore, DeviationResult
from pipewatch.metrics import MetricStatus, PipelineMetric


def make_metric(
    pipeline: str = "etl",
    duration: float = 10.0,
    errors: int = 0,
    rows: int = 100,
) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        duration_seconds=duration,
        error_count=errors,
        rows_processed=rows,
        timestamp=datetime.utcnow().isoformat(),
        status=MetricStatus.OK,
    )


def test_compute_and_store_creates_baseline():
    store = BaselineStore()
    metrics = [make_metric(duration=10.0, errors=2) for _ in range(5)]
    entry = store.compute_and_store("etl", metrics)
    assert entry.pipeline == "etl"
    assert entry.avg_duration == pytest.approx(10.0)
    assert entry.avg_error_rate == pytest.approx(2.0)
    assert entry.sample_count == 5


def test_compute_raises_on_empty_metrics():
    store = BaselineStore()
    with pytest.raises(ValueError, match="No metrics"):
        store.compute_and_store("etl", [])


def test_get_returns_none_when_no_baseline():
    store = BaselineStore()
    assert store.get("missing") is None


def test_get_returns_stored_baseline():
    store = BaselineStore()
    metrics = [make_metric(duration=5.0)]
    store.compute_and_store("pipe", metrics)
    entry = store.get("pipe")
    assert entry is not None
    assert entry.pipeline == "pipe"


def test_compare_no_baseline_returns_no_baseline_result():
    store = BaselineStore()
    metric = make_metric()
    result = store.compare(metric)
    assert result.has_baseline is False
    assert result.duration_delta_pct is None
    assert result.error_rate_delta_pct is None


def test_compare_above_baseline_positive_delta():
    store = BaselineStore()
    store.compute_and_store("etl", [make_metric(duration=10.0, errors=4)])
    metric = make_metric(duration=15.0, errors=8)
    result = store.compare(metric)
    assert result.has_baseline is True
    assert result.duration_delta_pct == pytest.approx(50.0)
    assert result.error_rate_delta_pct == pytest.approx(100.0)


def test_compare_zero_baseline_duration_skips_delta():
    store = BaselineStore()
    store.compute_and_store("etl", [make_metric(duration=0.0, errors=0)])
    metric = make_metric(duration=5.0, errors=0)
    result = store.compare(metric)
    assert result.duration_delta_pct is None
    assert result.error_rate_delta_pct is None


def test_all_pipelines_lists_stored_baselines():
    store = BaselineStore()
    store.compute_and_store("a", [make_metric(pipeline="a")])
    store.compute_and_store("b", [make_metric(pipeline="b")])
    assert set(store.all_pipelines()) == {"a", "b"}


def test_deviation_summary_no_baseline():
    result = DeviationResult(pipeline="x", duration_delta_pct=None, error_rate_delta_pct=None, has_baseline=False)
    assert "no baseline" in result.summary()


def test_deviation_summary_with_data():
    result = DeviationResult(pipeline="x", duration_delta_pct=25.0, error_rate_delta_pct=-10.0, has_baseline=True)
    summary = result.summary()
    assert "+25.0%" in summary
    assert "-10.0%" in summary


def test_baseline_entry_roundtrip():
    entry = BaselineEntry(pipeline="p", avg_duration=3.5, avg_error_rate=1.2, sample_count=7)
    d = entry.to_dict()
    restored = BaselineEntry.from_dict(d)
    assert restored.pipeline == entry.pipeline
    assert restored.avg_duration == entry.avg_duration
    assert restored.sample_count == entry.sample_count
