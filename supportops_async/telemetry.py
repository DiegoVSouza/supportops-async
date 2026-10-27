"""Opt-in, content-free OTLP tracing setup for API and worker processes."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlsplit

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter

_ATTACHED_EXPORTERS: set[tuple[int, str]] = set()
_ATTACHED_PROCESSORS: dict[tuple[int, str], BatchSpanProcessor] = {}
_OWNED_PROVIDERS: set[int] = set()


def _validate_configuration(service_name: str, endpoint: str) -> None:
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


def _attach_exporter(provider: TracerProvider, service_name: str, endpoint: str) -> bool:
    if provider.resource.attributes.get(SERVICE_NAME) != service_name:
        return False
    key = (id(provider), endpoint)
    if key not in _ATTACHED_EXPORTERS:
        exporter: SpanExporter = OTLPSpanExporter(endpoint=endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        _ATTACHED_EXPORTERS.add(key)
        _ATTACHED_PROCESSORS[key] = processor
    return True


def create_tracer_provider(
    service_name: str,
    endpoint: str,
    *,
    exporter_factory=OTLPSpanExporter,
) -> TracerProvider:
    """Create an OTLP provider after rejecting endpoints that could carry credentials."""
    _validate_configuration(service_name, endpoint)

    exporter: SpanExporter = exporter_factory(endpoint=endpoint)
    provider = TracerProvider(resource=Resource({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    _OWNED_PROVIDERS.add(id(provider))
    _ATTACHED_EXPORTERS.add((id(provider), endpoint))
    return provider


def configure_telemetry(service_name: str) -> TracerProvider | None:
    """Enable export only when an explicit OTLP traces endpoint is configured."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    if not endpoint:
        return None
    _validate_configuration(service_name, endpoint)
    # API instrumentation may install an SDK provider before the FastAPI
    # lifespan starts. Replacing that process-global provider is forbidden by
    # the OTel API, so attach the exporter to a compatible existing provider.
    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        if _attach_exporter(current, service_name, endpoint):
            return current
        logging.getLogger(__name__).warning("telemetry setup incomplete: provider identity mismatch")
        return None

    provider = create_tracer_provider(service_name, endpoint)
    trace.set_tracer_provider(provider)
    installed = trace.get_tracer_provider()
    if installed is provider:
        _ATTACHED_EXPORTERS.add((id(provider), endpoint))
        _OWNED_PROVIDERS.add(id(provider))
        return provider
    if isinstance(installed, TracerProvider) and _attach_exporter(installed, service_name, endpoint):
        return installed
    logging.getLogger(__name__).warning("telemetry setup incomplete: provider identity mismatch")
    return None


def shutdown_telemetry(provider: TracerProvider | None) -> bool:
    """Flush and close without raising telemetry failures into business shutdown."""
    if provider is None:
        return True
    try:
        flushed = provider.force_flush(timeout_millis=5_000)
        if id(provider) in _OWNED_PROVIDERS:
            provider.shutdown()
            _OWNED_PROVIDERS.discard(id(provider))
            for key in [key for key in _ATTACHED_EXPORTERS if key[0] == id(provider)]:
                _ATTACHED_EXPORTERS.discard(key)
        else:
            # A provider installed by the host belongs to that host. Shut down
            # only the exporter processor attached by this module.
            for key in [key for key in _ATTACHED_PROCESSORS if key[0] == id(provider)]:
                _ATTACHED_PROCESSORS.pop(key).shutdown()
                _ATTACHED_EXPORTERS.discard(key)
        return bool(flushed)
    except Exception:
        return False
