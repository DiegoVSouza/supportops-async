import os
from uuid import uuid4

import pytest

from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import SqsBroker
from supportops_async.store.postgres import PostgresTaskStore


@pytest.mark.integration
def test_postgres_idempotency_and_task_status():
    dsn = os.getenv("P04_POSTGRES_DSN")
    if not dsn:
        pytest.skip("P04_POSTGRES_DSN is not configured")
    store = PostgresTaskStore(dsn)
    idempotency_key = f"pg-integration-{uuid4().hex}"
    task, created = store.create({"steps": ["triage"]}, idempotency_key)
    replay, created_again = store.create({"steps": ["different"]}, idempotency_key)
    assert created and not created_again and replay.task_id == task.task_id


@pytest.mark.integration
def test_localstack_sqs_publish_consume_visibility_ack():
    endpoint = os.getenv("P04_LOCALSTACK_ENDPOINT")
    if not endpoint:
        pytest.skip("P04_LOCALSTACK_ENDPOINT is not configured")
    import boto3

    client = boto3.client("sqs", endpoint_url=endpoint, region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test")
    suffix = uuid4().hex
    queue_url = client.create_queue(QueueName=f"p04-integration-{suffix}")["QueueUrl"]
    dlq_url = client.create_queue(QueueName=f"p04-integration-dlq-{suffix}")["QueueUrl"]
    try:
        broker = SqsBroker(client, queue_url, dlq_url)
        broker.publish(BrokerMessage("integration-task"))
        handle = broker.consume()
        assert handle is not None and handle.message.task_id == "integration-task"
        broker.extend_visibility(handle, 30)
        broker.ack(handle)
    finally:
        client.delete_queue(QueueUrl=queue_url)
        client.delete_queue(QueueUrl=dlq_url)
