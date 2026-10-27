"""Opt-in, content-free OTLP tracing setup for API and worker processes."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter


def create_tracer_provider(
    service_name: str,
    endpoint: str,
    *,
    exporter_factory=OTLPSpanExporter,
) -> TracerProvider:
    """Create an OTLP provider after rejecting endpoints that could carry credentials."""
    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > 512:
        raise ValueError("invalid OTLP trace endpoint")
    if (
        not isinstance(service_name, str)
        or not service_name
        or len(service_name) > 64
        or any(not (char.isascii() and (char.isalnum() or char in "_.-")) for char in service_name)
    ):
        raise ValueError("invalid telemetry service name")
    try:
        parsed = urlsplit(endpoint)
        valid = (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
            and parsed.path.rstrip("/").endswith("/v1/traces")
        )
        _ = parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("invalid OTLP trace endpoint")

    exporter: SpanExporter = exporter_factory(endpoint=endpoint)
    provider = TracerProvider(resource=Resource({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider


def configure_telemetry(service_name: str) -> TracerProvider | None:
    """Enable export only when an explicit OTLP traces endpoint is configured."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    if not endpoint:
        return None
    provider = create_tracer_provider(service_name, endpoint)
    trace.set_tracer_provider(provider)
    return provider


def shutdown_telemetry(provider: TracerProvider | None) -> bool:
    """Flush and close without raising telemetry failures into business shutdown."""
    if provider is None:
        return True
    try:
        flushed = provider.force_flush(timeout_millis=5_000)
        provider.shutdown()
        return bool(flushed)
    except Exception:
        return False
