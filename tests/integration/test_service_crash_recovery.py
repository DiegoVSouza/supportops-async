"""Kill a real worker after its PostgreSQL effect commit, then recover via SQS."""

import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

import boto3
import psycopg
import pytest

from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import SqsBroker
from supportops_async.store.postgres import PostgresTaskStore
from supportops_async.worker import Worker


@pytest.mark.integration
def test_postgres_sqs_worker_kill_recovers_committed_effect():
    dsn = os.getenv("P04_POSTGRES_DSN")
    endpoint = os.getenv("P04_LOCALSTACK_ENDPOINT")
    if not dsn or not endpoint:
        pytest.skip("local PostgreSQL and LocalStack configuration required")
    client = boto3.client("sqs", endpoint_url=endpoint, region_name="us-east-1",
                          aws_access_key_id="test", aws_secret_access_key="test")
    suffix = uuid4().hex
    main = client.create_queue(QueueName=f"p04-crash-{suffix}")["QueueUrl"]
    dead = client.create_queue(QueueName=f"p04-crash-dlq-{suffix}")["QueueUrl"]
    store = PostgresTaskStore(dsn)
    task, _ = store.create({"steps": ["authorize", "complete"]}, f"crash-{suffix}")
    broker = SqsBroker(client, main, dead)
    broker.publish(BrokerMessage(task.task_id))
    child_code = '''
import os, time, boto3
from supportops_async.store.postgres import PostgresTaskStore
from supportops_async.queue.memory import SqsBroker
from supportops_async.worker import Worker
class CrashWindowStore(PostgresTaskStore):
    def apply_effect(self, task_id, step, result):
        committed = super().apply_effect(task_id, step, result)
        time.sleep(120)  # Parent terminates the process after observing the commit.
        return committed
c = boto3.client("sqs", endpoint_url=os.environ["P04_LOCALSTACK_ENDPOINT"],
                 region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test")
Worker(CrashWindowStore(os.environ["P04_POSTGRES_DSN"]),
       SqsBroker(c, os.environ["CRASH_QUEUE"], os.environ["CRASH_DLQ"]),
       worker_id="killed-worker", heartbeat_interval_seconds=1,
       visibility_timeout_seconds=2).run_once()
'''
    env = {**os.environ, "CRASH_QUEUE": main, "CRASH_DLQ": dead}
    child = subprocess.Popen([sys.executable, "-c", child_code], env=env,
                             cwd=Path(__file__).resolve().parents[2],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 15
        while store.effect(task.task_id, "1:authorize") is None:
            assert child.poll() is None, "worker exited before committing its effect"
            assert time.monotonic() < deadline, "worker did not reach the crash window"
            time.sleep(0.1)
        child.terminate()
        assert child.wait(timeout=5) != 0
        assert store.get(task.task_id).status.value == "running"
        # Observe the real 30-second database lease; do not bypass it with SQL updates.
        deadline = time.monotonic() + 35
        while True:
            with psycopg.connect(dsn) as conn:
                expired = conn.execute("SELECT lease_until <= now() FROM tasks WHERE task_id=%s",
                                       (task.task_id,)).fetchone()[0]
            if expired:
                break
            assert time.monotonic() < deadline, "worker lease never expired"
            time.sleep(0.2)
        calls = []
        recovered = Worker(store, broker, worker_id="recovery-worker",
                           runner=lambda payload, step: calls.append(step) or {"step": step})
        assert recovered.run_once(), "SQS did not redeliver the unacknowledged message"
        assert store.get(task.task_id).status.value == "done"
        assert store.get(task.task_id).attempts == 2
        assert calls == ["complete"], "committed authorize effect must not execute again"
        with psycopg.connect(dsn) as conn:
            assert conn.execute("SELECT count(*) FROM effects WHERE task_id=%s AND step=%s",
                                (task.task_id, "1:authorize")).fetchone()[0] == 1
        assert client.receive_message(QueueUrl=dead).get("Messages", []) == []
        print("service_crash_recovery=PASS killed_after_commit=true lease_expired=true "
              "sqs_redelivery=true resumed_steps=complete effect_rows=1 attempts=2")
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)
        client.delete_queue(QueueUrl=main)
        client.delete_queue(QueueUrl=dead)
