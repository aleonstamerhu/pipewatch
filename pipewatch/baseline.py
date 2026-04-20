"""Baseline management: store and compare pipeline metric baselines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class BaselineEntry:
    pipeline: str
    avg_duration: float
    avg_error_rate: float
    sample_count: int
    recorded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "avg_duration": self.avg_duration,
            "avg_error_rate": self.avg_error_rate,
            "sample_count": self.sample_count,
            "recorded_at": self.recorded_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "BaselineEntry":
        return BaselineEntry(
            pipeline=d["pipeline"],
            avg_duration=d["avg_duration"],
            avg_error_rate=d["avg_error_rate"],
            sample_count=d["sample_count"],
            recorded_at=d["recorded_at"],
        )


@dataclass
class DeviationResult:
    pipeline: str
    duration_delta_pct: Optional[float]
    error_rate_delta_pct: Optional[float]
    has_baseline: bool

    def summary(self) -> str:
        if not self.has_baseline:
            return f"{self.pipeline}: no baseline available"
        dur = f"{self.duration_delta_pct:+.1f}%" if self.duration_delta_pct is not None else "n/a"
        err = f"{self.error_rate_delta_pct:+.1f}%" if self.error_rate_delta_pct is not None else "n/a"
        return f"{self.pipeline}: duration {dur}, error_rate {err} vs baseline"


class BaselineStore:
    def __init__(self) -> None:
        self._baselines: Dict[str, BaselineEntry] = {}

    def compute_and_store(self, pipeline: str, metrics: List[PipelineMetric]) -> BaselineEntry:
        if not metrics:
            raise ValueError(f"No metrics provided for pipeline '{pipeline}'")
        avg_dur = sum(m.duration_seconds for m in metrics) / len(metrics)
        avg_err = sum(m.error_count for m in metrics) / len(metrics)
        entry = BaselineEntry(
            pipeline=pipeline,
            avg_duration=avg_dur,
            avg_error_rate=avg_err,
            sample_count=len(metrics),
        )
        self._baselines[pipeline] = entry
        return entry

    def get(self, pipeline: str) -> Optional[BaselineEntry]:
        return self._baselines.get(pipeline)

    def compare(self, metric: PipelineMetric) -> DeviationResult:
        baseline = self._baselines.get(metric.pipeline)
        if baseline is None:
            return DeviationResult(
                pipeline=metric.pipeline,
                duration_delta_pct=None,
                error_rate_delta_pct=None,
                has_baseline=False,
            )
        dur_delta = None
        if baseline.avg_duration > 0:
            dur_delta = ((metric.duration_seconds - baseline.avg_duration) / baseline.avg_duration) * 100
        err_delta = None
        if baseline.avg_error_rate > 0:
            err_delta = ((metric.error_count - baseline.avg_error_rate) / baseline.avg_error_rate) * 100
        return DeviationResult(
            pipeline=metric.pipeline,
            duration_delta_pct=dur_delta,
            error_rate_delta_pct=err_delta,
            has_baseline=True,
        )

    def all_pipelines(self) -> List[str]:
        return list(self._baselines.keys())
