import pytest

from supportops_async.events import EventPublisher, TaskEvent, drain_outbox
from supportops_async.store.sqlite import SQLiteTaskStore


def test_event_names_are_allowlisted_and_payload_serialized():
    class Client:
        def publish(self, **kwargs):
            self.message = kwargs["Message"]
            self.attributes = kwargs["MessageAttributes"]
            return {"MessageId": "m-1"}
    client = Client()
    publisher = EventPublisher(client, "local-topic")
    assert publisher.publish(TaskEvent("task.completed", "t1", {"ok": True})) == "m-1"
    assert '"task_id": "t1"' in client.message
    with pytest.raises(ValueError):
        publisher.publish(TaskEvent("task.deleted", "t1", {}))


def test_outbox_keeps_unsent_event_after_publish_failure_then_marks_delivery():
    store = SQLiteTaskStore()
    task, _ = store.create({}, "outbox")
    class Client:
        fail = True
        def publish(self, **kwargs):
            if self.fail:
                raise RuntimeError("temporary SNS outage")
            return {"MessageId": "m-2"}
    client = Client()
    publisher = EventPublisher(client, {"task.created": "topic-created"})
    with pytest.raises(RuntimeError):
        drain_outbox(store, publisher)
    assert len(store.pending_events()) == 1
    client.fail = False
    assert drain_outbox(store, publisher) == 1
    assert store.pending_events() == []
