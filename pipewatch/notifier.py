"""Notification channels for pipewatch alerts."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.alerts import Alert


@dataclass
class NotificationResult:
    channel: str
    success: bool
    message: str = ""


class BaseNotifier:
    def send(self, alert: Alert) -> NotificationResult:
        raise NotImplementedError


class ConsoleNotifier(BaseNotifier):
    """Prints alerts to stdout."""

    def send(self, alert: Alert) -> NotificationResult:
        print(f"[ALERT] {alert}")
        return NotificationResult(channel="console", success=True)


class LogNotifier(BaseNotifier):
    """Appends alerts to a log file."""

    def __init__(self, filepath: str):
        self.filepath = filepath

    def send(self, alert: Alert) -> NotificationResult:
        try:
            with open(self.filepath, "a") as f:
                f.write(str(alert) + "\n")
            return NotificationResult(channel="log", success=True)
        except OSError as e:
            return NotificationResult(channel="log", success=False, message=str(e))


class NotificationDispatcher:
    """Dispatches alerts to one or more notifiers."""

    def __init__(self, notifiers: Optional[List[BaseNotifier]] = None):
        self.notifiers: List[BaseNotifier] = notifiers or []

    def add(self, notifier: BaseNotifier) -> None:
        self.notifiers.append(notifier)

    def dispatch(self, alert: Alert) -> List[NotificationResult]:
        return [n.send(alert) for n in self.notifiers]

    def dispatch_all(self, alerts: List[Alert]) -> List[NotificationResult]:
        results = []
        for alert in alerts:
            results.extend(self.dispatch(alert))
        return results
