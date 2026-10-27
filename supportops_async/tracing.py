"""Minimal W3C trace context helpers; deliberately excludes baggage and tracestate."""

from __future__ import annotations

from collections.abc import Mapping

from opentelemetry import context, trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

_PROPAGATOR = TraceContextTextMapPropagator()
TRACER = trace.get_tracer("supportops_async")


def extract_trace_context(headers: Mapping[str, str] | None = None) -> context.Context:
    """Extract only a bounded traceparent value; ignore baggage and all other headers."""
    carrier: dict[str, str] = {}
    if headers:
        value = next((v for k, v in headers.items() if k.lower() == "traceparent"), None)
        if isinstance(value, str) and len(value) <= 128 and "\r" not in value and "\n" not in value:
            carrier["traceparent"] = value
    return _PROPAGATOR.extract(carrier)


def inject_traceparent(ctx: context.Context | None = None) -> str | None:
    carrier: dict[str, str] = {}
    _PROPAGATOR.inject(carrier, context=ctx)
    value = carrier.get("traceparent")
    return value if isinstance(value, str) and len(value) <= 128 else None


def safe_error_code(exc: BaseException) -> str:
    """Return a fixed operational category without incorporating exception content."""
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, PermissionError):
        return "authorization_failure"
    if isinstance(exc, (ConnectionError, OSError)):
        return "dependency_failure"
    if isinstance(exc, (ValueError, TypeError)):
        return "invalid_input"
    return "worker_failure"
