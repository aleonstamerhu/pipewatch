"""Audit log for pipeline metric events and alerts."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert


@dataclass
class AuditEntry:
    timestamp: datetime
    pipeline: str
    event_type: str  # 'metric' | 'alert'
    status: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "pipeline": self.pipeline,
            "event_type": self.event_type,
            "status": self.status,
            "detail": self.detail,
        }


class AuditLog:
    def __init__(self, max_entries: int = 500):
        self._entries: List[AuditEntry] = []
        self._max_entries = max_entries

    def record_metric(self, metric: PipelineMetric) -> None:
        entry = AuditEntry(
            timestamp=metric.timestamp,
            pipeline=metric.pipeline_name,
            event_type="metric",
            status=metric.status.value,
            detail=(
                f"rows={metric.rows_processed}, errors={metric.error_count}, "
                f"duration={metric.duration_seconds:.2f}s"
            ),
        )
        self._append(entry)

    def record_alert(self, alert: Alert) -> None:
        entry = AuditEntry(
            timestamp=alert.triggered_at,
            pipeline=alert.pipeline_name,
            event_type="alert",
            status=alert.severity,
            detail=alert.message,
        )
        self._append(entry)

    def _append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def entries(self, pipeline: Optional[str] = None) -> List[AuditEntry]:
        if pipeline is None:
            return list(self._entries)
        return [e for e in self._entries if e.pipeline == pipeline]

    def clear(self) -> None:
        self._entries.clear()
