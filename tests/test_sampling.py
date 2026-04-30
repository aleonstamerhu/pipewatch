"""Tests for pipewatch.sampling."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pytest

from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.sampling import (
    SamplingPolicy,
    SamplingResult,
    _apply_min_interval,
    sample_pipeline,
    sample_all,
)
from pipewatch.collector import MetricsCollector


def make_metric(
    pipeline: str = "pipe",
    status: MetricStatus = MetricStatus.OK,
    offset_seconds: float = 0.0,
) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        status=status,
        error_rate=0.0,
        duration_seconds=1.0,
        timestamp=datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds),
    )


def test_policy_default_values() -> None:
    p = SamplingPolicy()
    assert p.max_samples == 50
    assert p.min_interval_seconds == 0.0


def test_policy_rejects_zero_max_samples() -> None:
    with pytest.raises(ValueError, match="max_samples"):
        SamplingPolicy(max_samples=0)


def test_policy_rejects_negative_interval() -> None:
    with pytest.raises(ValueError, match="min_interval_seconds"):
        SamplingPolicy(min_interval_seconds=-1.0)


def test_sample_pipeline_empty_returns_none() -> None:
    assert sample_pipeline("pipe", []) is None


def test_sample_pipeline_keeps_up_to_max() -> None:
    metrics = [make_metric(offset_seconds=float(i)) for i in range(10)]
    result = sample_pipeline("pipe", metrics, SamplingPolicy(max_samples=5))
    assert result is not None
    assert result.sampled_count == 5
    assert result.original_count == 10
    # Should keep the most recent 5
    assert result.samples == metrics[-5:]


def test_sample_pipeline_fewer_than_max() -> None:
    metrics = [make_metric(offset_seconds=float(i)) for i in range(3)]
    result = sample_pipeline("pipe", metrics, SamplingPolicy(max_samples=10))
    assert result is not None
    assert result.sampled_count == 3


def test_apply_min_interval_drops_close_samples() -> None:
    metrics = [make_metric(offset_seconds=float(i)) for i in range(6)]
    # min_interval=2 → keep indices 0, 2, 4
    kept = _apply_min_interval(metrics, min_interval_seconds=2.0)
    assert len(kept) == 3
    assert kept[0] is metrics[0]
    assert kept[1] is metrics[2]
    assert kept[2] is metrics[4]


def test_apply_min_interval_zero_keeps_all() -> None:
    metrics = [make_metric(offset_seconds=float(i)) for i in range(5)]
    kept = _apply_min_interval(metrics, min_interval_seconds=0.0)
    assert kept == metrics


def test_sample_pipeline_summary_string() -> None:
    metrics = [make_metric(offset_seconds=float(i)) for i in range(4)]
    result = sample_pipeline("my_pipe", metrics, SamplingPolicy(max_samples=2))
    assert result is not None
    s = result.summary()
    assert "my_pipe" in s
    assert "2/4" in s


def test_sample_all_uses_collector() -> None:
    collector = MetricsCollector()
    for i in range(5):
        collector.record(make_metric("alpha", offset_seconds=float(i)))
    for i in range(3):
        collector.record(make_metric("beta", offset_seconds=float(i)))
    results = sample_all(collector, SamplingPolicy(max_samples=4))
    names = {r.pipeline for r in results}
    assert names == {"alpha", "beta"}
    alpha = next(r for r in results if r.pipeline == "alpha")
    assert alpha.sampled_count == 4


def test_sample_all_empty_collector() -> None:
    collector = MetricsCollector()
    results = sample_all(collector)
    assert results == []
