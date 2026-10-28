import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from supportops_async.api import app as api_module
from supportops_async.queue.contracts import BrokerMessage, MessageHandle
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import runner as worker_module
from supportops_async.worker.runner import Worker


def test_actual_failure_spans_export_without_exception_content(monkeypatch):
    payloads = []

    class Collector(BaseHTTPRequestHandler):
        def do_POST(self):
            payloads.append(self.rfile.read(int(self.headers['Content-Length'])))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Collector)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    provider = TracerProvider(resource=Resource.create({'service.name': 'p04-fixture'}))
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(
        endpoint=f'http://127.0.0.1:{server.server_port}/v1/traces', timeout=3
    )))
    monkeypatch.setattr(api_module, 'TRACER', provider.get_tracer('api'))
    monkeypatch.setattr(worker_module, 'TRACER', provider.get_tracer('worker'))
    sentinel = 'synthetic-private-exception-sentinel'

    class FailingStore(SQLiteTaskStore):
        def get(self, task_id):
            raise RuntimeError(sentinel)

    async def request():
        app = api_module.create_app(FailingStore(), InMemoryBroker())
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            await client.get('/tasks/failure')

    try:
        with pytest.raises(RuntimeError):
            asyncio.run(request())
        worker = Worker(FailingStore(), InMemoryBroker())
        with pytest.raises(RuntimeError):
            worker.process(MessageHandle('receipt', BrokerMessage('synthetic-task'), 1))
        assert provider.force_flush(timeout_millis=5000)
        spans = []
        for payload in payloads:
            assert sentinel.encode() not in payload
            request_proto = ExportTraceServiceRequest.FromString(payload)
            spans.extend(span for resource in request_proto.resource_spans for scope in resource.scope_spans for span in scope.spans)
        assert {span.name for span in spans} >= {'supportops.api.request', 'supportops.worker.process'}
        assert all(not span.events and not span.status.message for span in spans)
    finally:
        provider.shutdown()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
