import json

import pytest

from supportops_async.events import InMemoryEventInbox, NotificationConsumer


def notification(event_id: str = "evt-1", *, event_type: str = "task.completed") -> dict[str, str]:
    return {
        "Message": json.dumps(
            {"event_id": event_id, "event_type": event_type, "task_id": "task-1"}
        )
    }


def test_consumer_handles_duplicate_event_once() -> None:
    received: list[dict[str, str]] = []
    consumer = NotificationConsumer(InMemoryEventInbox(), received.append)

    assert consumer.consume(notification()) is True
    assert consumer.consume(notification()) is False
    assert len(received) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"Message": "{"},
        {"Message": json.dumps({"event_id": "evt-1", "event_type": "unknown", "task_id": "task-1"})},
        {"Message": json.dumps({"event_id": "evt-1", "event_type": "task.completed", "task_id": ""})},
    ],
)
def test_consumer_rejects_malformed_or_unsupported_events(payload: dict[str, str]) -> None:
    consumer = NotificationConsumer(InMemoryEventInbox(), lambda _: None)
    with pytest.raises(ValueError):
        consumer.consume(payload)


def test_consumer_does_not_mark_event_seen_when_handler_fails() -> None:
    calls = 0

    def handler(_: dict[str, str]) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary consumer failure")

    consumer = NotificationConsumer(InMemoryEventInbox(), handler)
    with pytest.raises(RuntimeError):
        consumer.consume(notification())

    assert consumer.consume(notification()) is True
    assert calls == 2
