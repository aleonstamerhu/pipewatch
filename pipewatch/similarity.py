"""Pipeline similarity detection based on metric history patterns."""

from dataclasses import dataclass
from typing import Optional
from pipewatch.collector import MetricsCollector
from pipewatch.correlation import _pearson


@dataclass
class SimilarityResult:
    pipeline_a: str
    pipeline_b: str
    score: float  # 0.0 to 1.0
    label: str

    def summary(self) -> str:
        return (
            f"{self.pipeline_a} <-> {self.pipeline_b}: "
            f"similarity={self.score:.2f} ({self.label})"
        )


def _similarity_label(score: float) -> str:
    if score >= 0.9:
        return "very similar"
    elif score >= 0.7:
        return "similar"
    elif score >= 0.4:
        return "somewhat similar"
    else:
        return "dissimilar"


def compute_similarity(
    collector: MetricsCollector,
    pipeline_a: str,
    pipeline_b: str,
    min_samples: int = 3,
) -> Optional[SimilarityResult]:
    """Compute similarity between two pipelines using error rate and duration."""
    history_a = collector.history(pipeline_a)
    history_b = collector.history(pipeline_b)

    if len(history_a) < min_samples or len(history_b) < min_samples:
        return None

    n = min(len(history_a), len(history_b))
    a_errors = [m.error_count for m in history_a[-n:]]
    b_errors = [m.error_count for m in history_b[-n:]]
    a_duration = [m.duration_seconds for m in history_a[-n:]]
    b_duration = [m.duration_seconds for m in history_b[-n:]]

    r_errors = _pearson(a_errors, b_errors)
    r_duration = _pearson(a_duration, b_duration)

    scores = [abs(r) for r in [r_errors, r_duration] if r is not None]
    if not scores:
        return None

    score = sum(scores) / len(scores)
    return SimilarityResult(
        pipeline_a=pipeline_a,
        pipeline_b=pipeline_b,
        score=round(score, 4),
        label=_similarity_label(score),
    )


def find_similar_pipelines(
    collector: MetricsCollector,
    pipeline: str,
    threshold: float = 0.7,
    min_samples: int = 3,
) -> list[SimilarityResult]:
    """Find all pipelines similar to the given one above a threshold."""
    all_pipelines = [p for p in collector.list_pipelines() if p != pipeline]
    results = []
    for other in all_pipelines:
        result = compute_similarity(collector, pipeline, other, min_samples)
        if result is not None and result.score >= threshold:
            results.append(result)
    results.sort(key=lambda r: r.score, reverse=True)
    return results
