from __future__ import annotations

import json
import os
import time
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


class RedisStreamBroker:
    """Redis Streams adapter with consumer-group recovery and a separate DLQ stream."""

    def __init__(self, client, queue_name: str, dlq_name: str | None = None,
                 *, visibility_timeout: int = 30, consumer_id: str | None = None) -> None:
        if not queue_name or visibility_timeout < 1:
            raise ValueError("queue name and positive visibility timeout are required")
        self.client = client
        self.queue_name = queue_name
        self.dlq_name = dlq_name or f"{queue_name}:dlq"
        self.group = "workers"
        self.consumer_id = consumer_id or f"{os.getpid()}-{uuid.uuid4()}"
        self.visibility_timeout = visibility_timeout
        self.attempts_key = f"{queue_name}:attempts"
        self.delayed_key = f"{queue_name}:delayed"
        try:
            self.client.xgroup_create(self.queue_name, self.group, id="0-0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def publish(self, msg: BrokerMessage) -> None:
        self.client.xadd(self.queue_name, {"task_id": msg.task_id, "attempts": 0})

    def _promote_due(self) -> None:
        self.client.eval(
            "local due=redis.call('ZRANGEBYSCORE',KEYS[1],'-inf',ARGV[1],'LIMIT',0,20); "
            "for _,item in ipairs(due) do "
            "if redis.call('ZREM',KEYS[1],item)==1 then "
            "local message=cjson.decode(item); "
            "redis.call('XADD',KEYS[2],'*','task_id',message.task_id,'attempts',message.attempts); "
            "end; end; return #due",
            2, self.delayed_key, self.queue_name, int(time.time() * 1000),
        )

    def consume(self) -> MessageHandle | None:
        self._promote_due()
        pending = self.client.xautoclaim(
            self.queue_name, self.group, self.consumer_id,
            self.visibility_timeout * 1000, start_id="0-0", count=1,
        )
        messages = pending[1]
        if not messages:
            batches = self.client.xreadgroup(
                self.group, self.consumer_id, {self.queue_name: ">"},
                count=1, block=1000,
            )
            messages = batches[0][1] if batches else []
        if not messages:
            return None
        message_id, values = messages[0]
        deliveries = self.client.hincrby(self.attempts_key, message_id, 1)
        attempts = int(values.get("attempts", 0)) + deliveries
        return MessageHandle(message_id, BrokerMessage(values["task_id"]), attempts)

    def ack(self, handle: MessageHandle) -> None:
        with self.client.pipeline(transaction=True) as pipe:
            pipe.xack(self.queue_name, self.group, handle.receipt)
            pipe.xdel(self.queue_name, handle.receipt)
            pipe.hdel(self.attempts_key, handle.receipt)
            pipe.execute()

    def nack(self, handle: MessageHandle, delay: int) -> None:
        if delay < 0:
            raise ValueError("delay must be non-negative")
        delayed = json.dumps({"task_id": handle.message.task_id, "attempts": handle.attempts})
        with self.client.pipeline(transaction=True) as pipe:
            pipe.zadd(self.delayed_key, {delayed: int(time.time() * 1000) + delay * 1000})
            pipe.xack(self.queue_name, self.group, handle.receipt)
            pipe.xdel(self.queue_name, handle.receipt)
            pipe.hdel(self.attempts_key, handle.receipt)
            pipe.execute()

    def extend_visibility(self, handle: MessageHandle, seconds: int) -> None:
        if seconds < 1:
            raise ValueError("visibility must be positive")
        self.visibility_timeout = seconds
        self.client.xclaim(
            self.queue_name, self.group, self.consumer_id, 0,
            [handle.receipt], idle=0,
        )

    def dead_letter(self, handle: MessageHandle) -> None:
        with self.client.pipeline(transaction=True) as pipe:
            pipe.xadd(self.dlq_name, {
                "task_id": handle.message.task_id,
                "attempts": handle.attempts,
                "source_id": handle.receipt,
            })
            pipe.xack(self.queue_name, self.group, handle.receipt)
            pipe.xdel(self.queue_name, handle.receipt)
            pipe.hdel(self.attempts_key, handle.receipt)
            pipe.execute()
