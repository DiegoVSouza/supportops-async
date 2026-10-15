from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class TaskEvent:
    event_type: str
    task_id: str
    payload: dict[str, Any]
    event_id: str | None = None


class TopicClient(Protocol):
    def publish(self, **kwargs: Any) -> dict[str, Any]: ...


class EventPublisher:
    ALLOWED = {"task.created", "task.completed", "task.failed"}

    def __init__(self, client: TopicClient, topic_arns: str | dict[str, str]) -> None:
        self.client, self.topic_arns = client, topic_arns

    def publish(self, event: TaskEvent) -> str:
        if event.event_type not in self.ALLOWED:
            raise ValueError("unsupported task event type")
        topic_arn = self.topic_arns if isinstance(self.topic_arns, str) else self.topic_arns[event.event_type]
        attributes = {"event_type": {"DataType": "String", "StringValue": event.event_type}}
        if event.event_id:
            attributes["event_id"] = {"DataType": "String", "StringValue": event.event_id}
        result = self.client.publish(TopicArn=topic_arn, Message=json.dumps(asdict(event), sort_keys=True), MessageAttributes=attributes)
        return result["MessageId"]


def drain_outbox(store: Any, publisher: EventPublisher, *, limit: int = 100) -> int:
    if limit < 1:
        raise ValueError("limit must be positive")
    delivered = 0
    for event_id, event_type, payload in store.pending_events()[:limit]:
        publisher.publish(TaskEvent(event_type, payload.get("task_id", ""), payload, event_id))
        store.mark_event_sent(event_id)
        delivered += 1
    return delivered
