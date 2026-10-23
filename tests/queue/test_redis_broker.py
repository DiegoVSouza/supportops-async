import os
import time
import uuid

import pytest
import redis

from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import RedisStreamBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker
from supportops_async.worker.runner import TransientFailure


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("P04_TEST_REDIS_URL"), reason="P04_TEST_REDIS_URL is not configured")
def test_redis_streams_retries_recovers_and_dead_letters():
    client = redis.Redis.from_url(os.environ["P04_TEST_REDIS_URL"], decode_responses=True)
    prefix = "p04-test-" + uuid.uuid4().hex
    queue, dead = prefix + ":tasks", prefix + ":dlq"
    first = RedisStreamBroker(client, queue, dead, visibility_timeout=1, consumer_id="first")

    try:
        first.publish(BrokerMessage("delayed"))
        original = first.consume()
        first.nack(original, 1)
        time.sleep(1.1)
        retry = first.consume()
        assert retry.message.task_id == "delayed"
        assert retry.attempts == 2
        first.ack(retry)

        first.publish(BrokerMessage("recover"))
        abandoned = first.consume()
        time.sleep(1.1)
        second = RedisStreamBroker(client, queue, dead, visibility_timeout=1, consumer_id="second")
        recovered = second.consume()
        assert recovered.message.task_id == "recover"
        assert recovered.receipt == abandoned.receipt
        assert recovered.attempts == 2
        second.dead_letter(recovered)
        assert client.xrange(dead)[0][1]["task_id"] == "recover"
        assert client.xrange(dead)[0][1]["attempts"] == "2"
        assert second.consume() is None

        store = SQLiteTaskStore()
        task, _ = store.create({"steps": ["retry"]}, prefix)
        second.publish(BrokerMessage(task.task_id))

        def fail_once(payload, step):
            raise TransientFailure("controlled Redis DLQ check")

        worker = Worker(
            store, second, runner=fail_once, max_attempts=1,
            heartbeat_interval_seconds=0.2, visibility_timeout_seconds=1,
        )
        assert worker.run_once()
        assert store.get(task.task_id).status.value == "failed"
        assert any(item[1]["task_id"] == task.task_id for item in client.xrange(dead))
    finally:
        client.delete(queue, dead, f"{queue}:attempts", f"{queue}:delayed")
        client.close()
