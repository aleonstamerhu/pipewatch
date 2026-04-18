"""Core metrics data structures for pipeline health monitoring."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PipelineMetric:
    """Represents a single health metric snapshot for a pipeline."""

    pipeline_name: str
    rows_processed: int
    error_count: int
    duration_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: MetricStatus = MetricStatus.UNKNOWN

    def compute_status(
        self,
        max_errors: int = 0,
        max_duration_seconds: float = 300.0,
    ) -> MetricStatus:
        """Derive status based on configurable thresholds."""
        if self.error_count > max_errors or self.duration_seconds > max_duration_seconds:
            self.status = MetricStatus.CRITICAL
        elif self.error_count == max_errors and self.duration_seconds <= max_duration_seconds * 0.8:
            self.status = MetricStatus.OK
        else:
            self.status = MetricStatus.WARNING
        return self.status

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "rows_processed": self.rows_processed,
            "error_count": self.error_count,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
        }
