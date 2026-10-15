import os

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
    task, created = store.create({"steps": ["triage"]}, "pg-integration")
    replay, created_again = store.create({"steps": ["different"]}, "pg-integration")
    assert created and not created_again and replay.task_id == task.task_id


@pytest.mark.integration
def test_localstack_sqs_publish_consume_visibility_ack():
    endpoint = os.getenv("P04_LOCALSTACK_ENDPOINT")
    if not endpoint:
        pytest.skip("P04_LOCALSTACK_ENDPOINT is not configured")
    import boto3

    client = boto3.client("sqs", endpoint_url=endpoint, region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test")
    queue_url = client.get_queue_url(QueueName=os.getenv("P04_QUEUE_NAME", "supportops-tasks"))["QueueUrl"]
    dlq_url = client.get_queue_url(QueueName=os.getenv("P04_DLQ_NAME", "supportops-tasks-dlq"))["QueueUrl"]
    broker = SqsBroker(client, queue_url, dlq_url)
    broker.publish(BrokerMessage("integration-task"))
    handle = broker.consume()
    assert handle is not None and handle.message.task_id == "integration-task"
    broker.extend_visibility(handle, 30)
    broker.ack(handle)
