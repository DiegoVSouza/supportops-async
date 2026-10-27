import json

import pytest

from supportops_async.queue.contracts import BrokerMessage, MessageHandle
from supportops_async.queue.memory import InMemoryBroker, RedisStreamBroker, SqsBroker


def test_memory_broker_requires_single_settlement_and_supports_redelivery():
    broker = InMemoryBroker()
    broker.publish(BrokerMessage("t1"))
    handle = broker.consume()
    assert handle.attempts == 1
    broker.nack(handle, 3)
    retry = broker.consume()
    assert retry.attempts == 2
    broker.ack(retry)
    with pytest.raises(ValueError):
        broker.ack(retry)


def test_broker_message_discards_invalid_trace_context():
    assert BrokerMessage("t-invalid", "not-a-w3c-traceparent").traceparent is None
    assert BrokerMessage("t-long", "0" * 129).traceparent is None


def test_sqs_adapter_uses_receive_count_and_safe_dead_letter():
    class Client:
        def __init__(self): self.calls = []
        def receive_message(self, **kwargs): return {"Messages": [{"Body": '{"task_id":"t1"}', "ReceiptHandle": "r", "Attributes": {"ApproximateReceiveCount": "4"}}]}
        def send_message(self, **kwargs): self.calls.append(("send", kwargs)); return {}
        def delete_message(self, **kwargs): self.calls.append(("delete", kwargs)); return {}
        def change_message_visibility(self, **kwargs): self.calls.append(("visibility", kwargs)); return {}

    client = Client()
    broker = SqsBroker(client, "source", "dlq")
    handle = broker.consume()
    assert handle.attempts == 4 and handle.message.task_id == "t1"
    broker.extend_visibility(handle, 35)
    assert client.calls[-1][0] == "visibility"
    assert client.calls[-1][1]["VisibilityTimeout"] == 35
    broker.dead_letter(handle)
    assert [call[0] for call in client.calls] == ["visibility", "send", "delete"]
    broker.nack(handle, 99999)
    assert client.calls[-1][1]["VisibilityTimeout"] == 43200


def test_sqs_traceparent_survives_publish_consume_and_dead_letter():
    class Client:
        def __init__(self): self.calls = []; self.body = None
        def send_message(self, **kwargs): self.calls.append(("send", kwargs)); return {}
        def receive_message(self, **kwargs): return {"Messages": [{"Body": self.body, "ReceiptHandle": "r"}]}
        def delete_message(self, **kwargs): self.calls.append(("delete", kwargs)); return {}
        def change_message_visibility(self, **kwargs): return {}

    client = Client()
    broker = SqsBroker(client, "source", "dlq")
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    broker.publish(BrokerMessage("t1", traceparent))
    client.body = client.calls[-1][1]["MessageBody"]
    handle = broker.consume()
    assert handle.message.traceparent == traceparent
    broker.dead_letter(handle)
    assert json.loads(client.calls[-2][1]["MessageBody"]) == {
        "task_id": "t1", "attempts": 1, "traceparent": traceparent
    }


def test_redis_stream_traceparent_survives_publish_consume_retry_and_dlq():
    class Pipeline:
        def __init__(self, client): self.client = client
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def zadd(self, key, mapping): self.client.delayed = next(iter(mapping))
        def xack(self, *args): return self
        def xdel(self, *args): return self
        def hdel(self, *args): return self
        def xadd(self, stream, values): self.client.dead.append((stream, values)); return self
        def execute(self): return []

    class Client:
        def __init__(self): self.entries = []; self.delayed = None; self.dead = []; self.script = ""
        def xgroup_create(self, *args, **kwargs): pass
        def xadd(self, stream, values): self.entries.append(("1-0", values)); return "1-0"
        def eval(self, script, *args): self.script = script; return 0
        def xautoclaim(self, *args, **kwargs): return ("0-0", [], None)
        def xreadgroup(self, *args, **kwargs): return [("q", self.entries)] if self.entries else []
        def hincrby(self, *args): return 1
        def pipeline(self, **kwargs): return Pipeline(self)

    client = Client()
    broker = RedisStreamBroker(client, "q")
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    broker.publish(BrokerMessage("t1", traceparent))
    assert client.entries[-1][1]["traceparent"] == traceparent
    handle = broker.consume()
    assert handle.message.traceparent == traceparent
    broker.nack(handle, 1)
    assert json.loads(client.delayed)["traceparent"] == traceparent
    broker._promote_due()
    assert "message.traceparent" in client.script
    client.entries = [("2-0", {"task_id": "legacy", "attempts": "0"})]
    legacy = broker.consume()
    assert legacy.message.task_id == "legacy" and legacy.message.traceparent is None
    handle = MessageHandle("1-0", BrokerMessage("t1", traceparent), 2)
    broker.dead_letter(handle)
    assert client.dead[-1][1]["traceparent"] == traceparent
