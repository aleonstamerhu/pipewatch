"""Metric sampling: downsample or rate-limit metric history for analysis."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import PipelineMetric


@dataclass
class SamplingPolicy:
    """Controls how many samples to retain and the minimum spacing (seconds)."""
    max_samples: int = 50
    min_interval_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.max_samples < 1:
            raise ValueError("max_samples must be >= 1")
        if self.min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be >= 0")


@dataclass
class SamplingResult:
    pipeline: str
    original_count: int
    sampled_count: int
    samples: List[PipelineMetric]

    def summary(self) -> str:
        return (
            f"{self.pipeline}: {self.sampled_count}/{self.original_count} samples retained"
        )


def _apply_min_interval(
    metrics: List[PipelineMetric], min_interval_seconds: float
) -> List[PipelineMetric]:
    """Drop metrics that are too close together in time (keep first in each window)."""
    if min_interval_seconds <= 0:
        return list(metrics)
    kept: List[PipelineMetric] = []
    last_ts: Optional[float] = None
    for m in metrics:
        ts = m.timestamp.timestamp()
        if last_ts is None or (ts - last_ts) >= min_interval_seconds:
            kept.append(m)
            last_ts = ts
    return kept


def sample_pipeline(
    pipeline: str,
    metrics: List[PipelineMetric],
    policy: Optional[SamplingPolicy] = None,
) -> Optional[SamplingResult]:
    """Apply sampling policy to a list of metrics for one pipeline."""
    if not metrics:
        return None
    if policy is None:
        policy = SamplingPolicy()
    original_count = len(metrics)
    spaced = _apply_min_interval(metrics, policy.min_interval_seconds)
    # Keep the most recent max_samples
    sampled = spaced[-policy.max_samples :]
    return SamplingResult(
        pipeline=pipeline,
        original_count=original_count,
        sampled_count=len(sampled),
        samples=sampled,
    )


def sample_all(
    collector: "MetricsCollector",  # type: ignore[name-defined]  # noqa: F821
    policy: Optional[SamplingPolicy] = None,
) -> List[SamplingResult]:
    """Apply sampling to every pipeline tracked by a collector."""
    from pipewatch.collector import MetricsCollector  # local import to avoid cycle

    results: List[SamplingResult] = []
    for pipeline in collector.pipelines():
        history = collector.history(pipeline)
        result = sample_pipeline(pipeline, history, policy)
        if result is not None:
            results.append(result)
    return results
