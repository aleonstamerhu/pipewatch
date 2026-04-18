"""Alert rules and notification logic for pipeline metrics."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional
from pipewatch.metrics import MetricStatus, PipelineMetric


@dataclass
class AlertRule:
    """Defines a condition that triggers an alert."""
    name: str
    pipeline: str
    condition: Callable[[PipelineMetric], bool]
    message: str
    severity: str = "warning"  # warning | critical


@dataclass
class Alert:
    """Represents a fired alert."""
    rule_name: str
    pipeline: str
    severity: str
    message: str
    metric: PipelineMetric

    def __str__(self) -> str:
        return (
            f"[{self.severity.upper()}] {self.rule_name} on '{self.pipeline}': "
            f"{self.message} (status={self.metric.status.value})"
        )


class AlertEngine:
    """Evaluates alert rules against pipeline metrics."""

    def __init__(self) -> None:
        self._rules: List[AlertRule] = []

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule."""
        self._rules.append(rule)

    def evaluate(self, metric: PipelineMetric) -> List[Alert]:
        """Evaluate all matching rules against a metric, return fired alerts."""
        fired: List[Alert] = []
        for rule in self._rules:
            if rule.pipeline != metric.pipeline_name:
                continue
            if rule.condition(metric):
                fired.append(Alert(
                    rule_name=rule.name,
                    pipeline=metric.pipeline_name,
                    severity=rule.severity,
                    message=rule.message,
                    metric=metric,
                ))
        return fired

    def evaluate_all(self, metrics: List[PipelineMetric]) -> List[Alert]:
        """Evaluate rules across multiple metrics."""
        alerts: List[Alert] = []
        for metric in metrics:
            alerts.extend(self.evaluate(metric))
        return alerts
