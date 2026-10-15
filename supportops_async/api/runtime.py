from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

import boto3

from supportops_async.api import create_app
from supportops_async.events import EventPublisher
from supportops_async.queue.memory import SqsBroker
from supportops_async.store.postgres import PostgresTaskStore


def aws_client(service: str):
    return boto3.client(
        service,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        endpoint_url=os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    )


def runtime_components():
    dsn = os.environ["P04_DATABASE_URL"]
    sqs = aws_client("sqs")
    sns = aws_client("sns")
    queue_url = sqs.get_queue_url(QueueName=os.getenv("P04_QUEUE_NAME", "supportops-tasks"))["QueueUrl"]
    dlq_url = sqs.get_queue_url(QueueName=os.getenv("P04_DLQ_NAME", "supportops-tasks-dlq"))["QueueUrl"]
    # LocalStack path-style URLs default to localhost; inside Compose they must resolve to the service.
    endpoint = urlsplit(os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566"))
    def internal_url(value: str) -> str:
        parts = urlsplit(value)
        return urlunsplit((parts.scheme, endpoint.netloc, parts.path, parts.query, parts.fragment))
    queue_url, dlq_url = internal_url(queue_url), internal_url(dlq_url)
    topic_arns = {
        event_type: os.environ[f"P04_{event_type.upper().replace('.', '_')}_TOPIC_ARN"]
        for event_type in ("task.created", "task.completed", "task.failed")
    }
    store = PostgresTaskStore(dsn)
    return store, SqsBroker(sqs, queue_url, dlq_url), EventPublisher(sns, topic_arns)


store, broker, events = runtime_components()
app = create_app(store, broker, events)
