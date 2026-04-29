"""Integration bridge: suppress alerts before dispatching via NotifierDispatcher."""
from __future__ import annotations

from typing import Optional

from pipewatch.alerts import Alert
from pipewatch.notifier import BaseNotifier, NotificationResult, NotifierDispatcher
from pipewatch.suppression import SuppressionStore


class SuppressingDispatcher:
    """Wraps a NotifierDispatcher and skips suppressed alerts."""

    def __init__(self, dispatcher: NotifierDispatcher, store: SuppressionStore) -> None:
        self._dispatcher = dispatcher
        self._store = store
        self.suppressed_count: int = 0

    def send(self, alert: Alert) -> list[NotificationResult]:
        if self._store.is_suppressed(alert):
            self.suppressed_count += 1
            return [
                NotificationResult(
                    notifier="suppression",
                    success=True,
                    message=f"Alert for '{alert.pipeline}' suppressed.",
                )
            ]
        return self._dispatcher.send(alert)

    def send_all(self, alerts: list[Alert]) -> dict[str, list[NotificationResult]]:
        results: dict[str, list[NotificationResult]] = {}
        for alert in alerts:
            key = f"{alert.pipeline}:{alert.severity}"
            results[key] = self.send(alert)
        return results

    @property
    def suppressed(self) -> int:
        return self.suppressed_count


def build_suppressing_dispatcher(
    notifiers: list[BaseNotifier],
    store: Optional[SuppressionStore] = None,
) -> SuppressingDispatcher:
    """Convenience factory."""
    dispatcher = NotifierDispatcher(notifiers)
    return SuppressingDispatcher(dispatcher, store or SuppressionStore())
