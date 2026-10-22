import json
import os
import threading
import time
import uuid

import boto3
from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import SqsBroker
from supportops_async.store.postgres import PostgresTaskStore
from supportops_async.worker import Worker
from supportops_async.worker.runner import TransientFailure

DSN = os.environ["P04_POSTGRES_DSN"]
ENDPOINT = os.environ["P04_LOCALSTACK_ENDPOINT"]
client = boto3.client("sqs", endpoint_url=ENDPOINT, region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test")
store = PostgresTaskStore(DSN)
created = []

def queues(prefix):
    suffix = uuid.uuid4().hex[:10]
    main = client.create_queue(QueueName=f"{prefix}-{suffix}")["QueueUrl"]
    dead = client.create_queue(QueueName=f"{prefix}-dlq-{suffix}")["QueueUrl"]
    created.extend([main, dead])
    return SqsBroker(client, main, dead)

try:
    long_broker = queues("p04-phase008-long")
    long_task, _ = store.create({"steps": ["long"], "step_delay_seconds": 31.5}, f"phase008-long-{uuid.uuid4().hex}")
    long_broker.publish(BrokerMessage(long_task.task_id))
    def long_runner(payload, step):
        time.sleep(payload["step_delay_seconds"])
        return {"step": step, "outcome": "simulated-long"}
    worker = Worker(store, long_broker, runner=long_runner, worker_id="phase008-long-worker", heartbeat_interval_seconds=2, visibility_timeout_seconds=5)
    thread = threading.Thread(target=lambda: worker.run_once(), daemon=True)
    started = time.monotonic()
    thread.start()
    time.sleep(30.5)
    competing_claim = store.claim(long_task.task_id, "phase008-competitor")
    thread.join(timeout=8)
    if thread.is_alive():
        raise AssertionError("long-step worker did not finish")
    if competing_claim:
        raise AssertionError("competing worker claimed task during long step")
    long_record = store.get(long_task.task_id)
    if long_record.status.value != "done" or long_record.attempts != 1:
        raise AssertionError(f"long task unexpected state: {long_record}")
    effect = store.effect(long_task.task_id, "1:long")
    if effect is None:
        raise AssertionError("long task effect was not persisted")
    print(f"long_step: PASS elapsed_seconds={time.monotonic()-started:.1f} competing_claim={competing_claim} task_status={long_record.status.value} attempts={long_record.attempts} effect_persisted=true")

    duplicate_broker = queues("p04-phase008-dup")
    duplicate_task, _ = store.create({"steps": ["effect"], "operation_id": "phase008-idempotent"}, f"phase008-dup-{uuid.uuid4().hex}")
    duplicate_broker.publish(BrokerMessage(duplicate_task.task_id))
    duplicate_broker.publish(BrokerMessage(duplicate_task.task_id))
    duplicate_worker = Worker(store, duplicate_broker, worker_id="phase008-duplicate-worker")
    assert duplicate_worker.run_once() and duplicate_worker.run_once()
    duplicate_record = store.get(duplicate_task.task_id)
    duplicate_effect = store.effect(duplicate_task.task_id, "1:effect")
    if duplicate_record.status.value != "done" or duplicate_record.attempts != 1 or duplicate_effect is None:
        raise AssertionError("duplicate delivery was not idempotent")
    print(f"duplicate_delivery: PASS task_status={duplicate_record.status.value} claims={duplicate_record.attempts} one_effect_record=true")

    retry_broker = queues("p04-phase008-retry")
    retry_task, _ = store.create({"steps": ["retry"]}, f"phase008-retry-{uuid.uuid4().hex}")
    retry_broker.publish(BrokerMessage(retry_task.task_id))
    def fail_transient(payload, step):
        raise TransientFailure("phase 008 controlled retry")
    retry_worker = Worker(store, retry_broker, runner=fail_transient, worker_id="phase008-retry-worker", max_attempts=3, base_delay=1)
    for delay in (1.5, 2.5, 0):
        retry_worker.run_once()
        if store.get(retry_task.task_id).status.value != "failed" and delay:
            time.sleep(delay)
    retry_record = store.get(retry_task.task_id)
    dead = client.receive_message(QueueUrl=retry_broker.dlq_url, MaxNumberOfMessages=2, WaitTimeSeconds=2)
    messages = dead.get("Messages", [])
    if retry_record.status.value != "failed" or retry_record.attempts != 3 or len(messages) != 1:
        raise AssertionError(f"retry/DLQ unexpected status={retry_record.status.value} attempts={retry_record.attempts} dlq_count={len(messages)}")
    dlq_body = json.loads(messages[0]["Body"])
    if dlq_body.get("task_id") != retry_task.task_id or dlq_body.get("attempts") != 3:
        raise AssertionError(f"unexpected DLQ payload: {dlq_body}")
    client.delete_message(QueueUrl=retry_broker.dlq_url, ReceiptHandle=messages[0]["ReceiptHandle"])
    print(f"retry_dlq: PASS task_status={retry_record.status.value} attempts={retry_record.attempts} dlq_messages=1")
finally:
    for queue_url in created:
        client.delete_queue(QueueUrl=queue_url)
