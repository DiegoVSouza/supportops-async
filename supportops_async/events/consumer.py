from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import Any, Protocol


class EventInbox(Protocol):
    def handle_once(self, event_id: str, event: dict[str, Any], handler: Callable[[dict[str, Any]], None]) -> bool: ...


class InMemoryEventInbox:
    """Example deduplicating inbox for the local notification consumer."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def handle_once(self, event_id: str, event: dict[str, Any], handler: Callable[[dict[str, Any]], None]) -> bool:
        if not event_id:
            raise ValueError("event_id is required")
        with self._lock:
            if event_id in self._seen:
                return False
            handler(event)
            self._seen.add(event_id)
            return True


class NotificationConsumer:
    """Example SNS notification consumer with an injected durable inbox contract."""

    def __init__(self, inbox: EventInbox, handler: Callable[[dict[str, Any]], None]) -> None:
        self.inbox, self.handler = inbox, handler

    def consume(self, notification: dict[str, Any]) -> bool:
        try:
            event = json.loads(notification["Message"])
            event_id = event["event_id"]
            event_type = event["event_type"]
            task_id = event["task_id"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid SNS task notification") from exc
        if event_type not in {"task.created", "task.completed", "task.failed"} or not task_id:
            raise ValueError("invalid task notification contract")
        return self.inbox.handle_once(event_id, event, self.handler)
