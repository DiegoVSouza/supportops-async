import asyncio

import httpx
import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from supportops_async.api import app as api_module
from supportops_async.queue.contracts import BrokerMessage, MessageHandle
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import runner as worker_module
from supportops_async.worker.runner import Worker


def memory_tracer(monkeypatch, module, name):
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": name}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(module, "TRACER", provider.get_tracer(name))
    return exporter


def test_api_middleware_span_status_omits_exception_message(monkeypatch):
    exporter = memory_tracer(monkeypatch, api_module, "p04-api-privacy-test")
    sentinel = "private-api-status-sentinel"

    class FailingStore(SQLiteTaskStore):
        def get(self, task_id):
            raise RuntimeError(sentinel)

    app = api_module.create_app(FailingStore(), InMemoryBroker())

    async def request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/tasks/failure")

    with pytest.raises(RuntimeError, match=sentinel):
        asyncio.run(request())

    span = exporter.get_finished_spans()[0]
    assert span.name == "supportops.api.request"
    assert span.status.status_code.name == "ERROR"
    assert span.status.description is None
    assert span.attributes["supportops.error.category"] == "worker_failure"
    assert span.events == ()
    assert sentinel not in repr(span)


def test_worker_process_span_status_omits_exception_message(monkeypatch):
    exporter = memory_tracer(monkeypatch, worker_module, "p04-worker-privacy-test")
    sentinel = "private-worker-status-sentinel"

    class FailingStore:
        def get(self, task_id):
            raise RuntimeError(sentinel)

    handle = MessageHandle("receipt", BrokerMessage("synthetic-task"), 1)
    worker = Worker(FailingStore(), InMemoryBroker())

    with pytest.raises(RuntimeError, match=sentinel):
        worker.process(handle)

    span = exporter.get_finished_spans()[0]
    assert span.name == "supportops.worker.process"
    assert span.status.status_code.name == "ERROR"
    assert span.status.description is None
    assert span.attributes["supportops.error.category"] == "worker_failure"
    assert span.events == ()
    assert sentinel not in repr(span)
