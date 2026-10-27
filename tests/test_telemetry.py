from __future__ import annotations

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from supportops_async.telemetry import create_tracer_provider, shutdown_telemetry


def test_otlp_provider_exports_only_explicit_span_attributes() -> None:
    exporter = InMemorySpanExporter()
    provider = create_tracer_provider(
        "test-service",
        "http://jaeger:4318/v1/traces",
        exporter_factory=lambda *, endpoint: exporter,
    )
    with provider.get_tracer("test").start_as_current_span("safe.operation") as span:
        span.set_attribute("supportops.error.category", "dependency_failure")

    assert shutdown_telemetry(provider)
    finished = exporter.get_finished_spans()
    assert len(finished) == 1
    assert finished[0].name == "safe.operation"
    assert finished[0].resource.attributes["service.name"] == "test-service"
    assert finished[0].attributes == {"supportops.error.category": "dependency_failure"}


@pytest.mark.parametrize(
    "endpoint",
    [
        "file:///tmp/traces",
        "http://user:password@jaeger:4318/v1/traces",
        "http://jaeger:4318/v1/traces?token=secret",
        "http://jaeger:4318/v1/traces#fragment",
        "http://jaeger:4318/other",
        "http://jaeger:bad/v1/traces",
    ],
)
def test_otlp_endpoint_rejects_credentials_query_and_invalid_targets(endpoint: str) -> None:
    with pytest.raises(ValueError, match="invalid OTLP trace endpoint"):
        create_tracer_provider("test-service", endpoint)


def test_shutdown_without_exporter_is_a_safe_noop() -> None:
    assert shutdown_telemetry(None)
