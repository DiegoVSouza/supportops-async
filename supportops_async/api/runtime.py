from __future__ import annotations

import os

import boto3
import redis

from supportops_async.api import create_app
from supportops_async.events import EventPublisher
from supportops_async.queue.memory import RedisStreamBroker
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
    sns = aws_client("sns")
    redis_client = redis.Redis.from_url(os.environ["P04_REDIS_URL"], decode_responses=True)
    broker = RedisStreamBroker(
        redis_client,
        os.getenv("P04_QUEUE_NAME", "supportops-tasks"),
        os.getenv("P04_DLQ_NAME", "supportops-tasks:dlq"),
        visibility_timeout=int(os.getenv("P04_VISIBILITY_TIMEOUT", "30")),
    )
    topic_arns = {
        event_type: os.environ[f"P04_{event_type.upper().replace('.', '_')}_TOPIC_ARN"]
        for event_type in ("task.created", "task.completed", "task.failed")
    }
    store = PostgresTaskStore(dsn)
    return store, broker, EventPublisher(sns, topic_arns)


store, broker, events = runtime_components()
app = create_app(store, broker, events)
