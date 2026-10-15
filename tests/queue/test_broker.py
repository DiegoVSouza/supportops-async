import pytest

from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import InMemoryBroker, SqsBroker


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
    broker.dead_letter(handle)
    assert [call[0] for call in client.calls] == ["send", "delete"]
    broker.nack(handle, 99999)
    assert client.calls[-1][1]["VisibilityTimeout"] == 43200
