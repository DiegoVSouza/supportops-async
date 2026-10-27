from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Response, status
from opentelemetry import trace
from pydantic import BaseModel, ConfigDict, Field

from supportops_async.queue.contracts import Broker, BrokerMessage
from supportops_async.store.models import TaskStore
from supportops_async.events.events import EventPublisher, drain_outbox
from supportops_async.tracing import TRACER, extract_trace_context, inject_traceparent, safe_error_code
from supportops_async.telemetry import configure_telemetry, shutdown_telemetry

logger = logging.getLogger(__name__)


class CreateTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload: dict[str, Any] = Field(default_factory=dict)
    steps: list[str] = Field(default_factory=lambda: ["triage", "resolve"], min_length=1, max_length=20)


def create_app(store: TaskStore, broker: Broker, events: EventPublisher | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        provider = configure_telemetry(os.getenv("OTEL_SERVICE_NAME", "supportops-async-api"))
        try:
            yield
        finally:
            if not shutdown_telemetry(provider):
                # Deliberately omit exporter exception content and endpoint details.
                logger.warning("telemetry shutdown incomplete")

    app = FastAPI(title="SupportOps Async API", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def trace_request(request, call_next):
        parent = extract_trace_context(request.headers)
        with TRACER.start_as_current_span("supportops.api.request", context=parent, record_exception=False) as span:
            method = request.method if request.method in {"GET", "POST", "PUT", "DELETE", "PATCH"} else "OTHER"
            span.set_attribute("supportops.http.method", method)
            try:
                response = await call_next(request)
            except Exception as exc:
                span.set_attribute("supportops.error.category", safe_error_code(exc))
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
            span.set_attribute("supportops.http.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
            return response

    @app.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
    def create_task(body: CreateTask, response: Response, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, str]:
        if not idempotency_key:
            raise HTTPException(400, "Idempotency-Key header is required")
        payload = {**body.payload, "steps": body.steps}
        try:
            task, created = store.create(payload, idempotency_key)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        # Publish on every retry; duplicate messages are safe by task/effect idempotency.
        try:
            if task.status.value in {"queued", "retrying"}:
                broker.publish(BrokerMessage(task.task_id, inject_traceparent()))
        except Exception as exc:
            raise HTTPException(503, "task persisted but enqueue failed; retry with the same key") from exc
        if events is not None:
            try:
                drain_outbox(store, events)
            except Exception:
                # Keep unsent entries durable; the worker retries the outbox on its next poll.
                pass
        response.headers["Idempotency-Replayed"] = "false" if created else "true"
        return {"task_id": task.task_id}

    @app.get("/tasks/{task_id}")
    def get_task(task_id: str) -> dict[str, Any]:
        task = store.get(task_id)
        if task is None:
            raise HTTPException(404, "task not found")
        result: dict[str, Any] = {"task_id": task.task_id, "status": task.status.value, "step": task.step, "progress": task.progress}
        if task.result is not None:
            result["result"] = task.result
        if task.error is not None:
            result["error"] = task.error
        return result

    @app.post("/tasks/{task_id}/cancel", status_code=202)
    def cancel_task(task_id: str) -> dict[str, str]:
        task = store.get(task_id)
        if task is None:
            raise HTTPException(404, "task not found")
        if not store.cancel(task_id):
            raise HTTPException(409, f"cannot cancel task in {task.status.value} state")
        return {"task_id": task_id, "status": "cancelled"}

    return app
