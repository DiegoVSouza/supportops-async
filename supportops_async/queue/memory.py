from __future__ import annotations

import json
import uuid
from collections import deque
from dataclasses import dataclass

from .contracts import BrokerMessage, MessageHandle


@dataclass
class _Entry:
    message: BrokerMessage
    attempts: int = 0


class InMemoryBroker:
    """Deterministic at-least-once broker double for local tests."""

    def __init__(self) -> None:
        self._pending: deque[_Entry] = deque()
        self._inflight: dict[str, _Entry] = {}
        self.dead_letters: list[BrokerMessage] = []
        self.nack_delays: list[int] = []

    def publish(self, msg: BrokerMessage) -> None:
        self._pending.append(_Entry(msg))

    def consume(self) -> MessageHandle | None:
        if not self._pending:
            return None
        entry = self._pending.popleft()
        entry.attempts += 1
        receipt = str(uuid.uuid4())
        self._inflight[receipt] = entry
        return MessageHandle(receipt, entry.message, entry.attempts)

    def ack(self, handle: MessageHandle) -> None:
        self._require(handle)
        del self._inflight[handle.receipt]

    def nack(self, handle: MessageHandle, delay: int) -> None:
        if delay < 0:
            raise ValueError("delay must be non-negative")
        self._pending.append(self._require(handle))
        self.nack_delays.append(delay)
        del self._inflight[handle.receipt]

    def extend_visibility(self, handle: MessageHandle, seconds: int) -> None:
        if seconds < 1:
            raise ValueError("visibility must be positive")
        self._require(handle)

    def dead_letter(self, handle: MessageHandle) -> None:
        entry = self._require(handle)
        self.dead_letters.append(entry.message)
        del self._inflight[handle.receipt]

    def _require(self, handle: MessageHandle) -> _Entry:
        try:
            return self._inflight[handle.receipt]
        except KeyError as exc:
            raise ValueError("unknown or already settled message handle") from exc


class SqsBroker:
    """SQS adapter; inject a boto3 client and queue URLs, no credential discovery in tests."""

    def __init__(self, client: object, queue_url: str, dlq_url: str) -> None:
        self.client = client
        self.queue_url = queue_url
        self.dlq_url = dlq_url

    def publish(self, msg: BrokerMessage) -> None:
        self.client.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps({"task_id": msg.task_id}))

    def consume(self) -> MessageHandle | None:
        response = self.client.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1, AttributeNames=["ApproximateReceiveCount"])
        messages = response.get("Messages", [])
        if not messages:
            return None
        raw = messages[0]
        return MessageHandle(raw["ReceiptHandle"], BrokerMessage(json.loads(raw["Body"])["task_id"]), int(raw.get("Attributes", {}).get("ApproximateReceiveCount", "1")))

    def ack(self, handle: MessageHandle) -> None:
        self.client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=handle.receipt)

    def nack(self, handle: MessageHandle, delay: int) -> None:
        self.client.change_message_visibility(QueueUrl=self.queue_url, ReceiptHandle=handle.receipt, VisibilityTimeout=max(0, min(delay, 43200)))

    def extend_visibility(self, handle: MessageHandle, seconds: int) -> None:
        self.client.change_message_visibility(QueueUrl=self.queue_url, ReceiptHandle=handle.receipt, VisibilityTimeout=max(1, min(seconds, 43200)))

    def dead_letter(self, handle: MessageHandle) -> None:
        self.client.send_message(QueueUrl=self.dlq_url, MessageBody=json.dumps({"task_id": handle.message.task_id, "attempts": handle.attempts}))
        self.ack(handle)
