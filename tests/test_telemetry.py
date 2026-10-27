from __future__ import annotations

import pytest
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import ProxyTracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from supportops_async import telemetry
from supportops_async.telemetry import configure_telemetry, create_tracer_provider, shutdown_telemetry


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


def test_configure_without_endpoint_keeps_global_provider_untouched(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", raising=False)
    replaced = []
    monkeypatch.setattr(telemetry.trace, "set_tracer_provider", replaced.append)

    assert configure_telemetry("supportops-async-api") is None
    assert replaced == []


def test_existing_sdk_provider_gets_one_exporter_without_global_replacement(monkeypatch) -> None:
    provider = TracerProvider(resource=Resource({SERVICE_NAME: "supportops-async-api"}))
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://jaeger:4318/v1/traces")
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: provider)
    replaced = []
    monkeypatch.setattr(telemetry.trace, "set_tracer_provider", replaced.append)
    monkeypatch.setattr(telemetry, "OTLPSpanExporter", lambda **_: InMemorySpanExporter())

    assert configure_telemetry("supportops-async-api") is provider
    assert configure_telemetry("supportops-async-api") is provider
    assert replaced == []
    assert len(telemetry._ATTACHED_PROCESSORS) == 1
    assert shutdown_telemetry(provider)
    assert telemetry._ATTACHED_PROCESSORS == {}
    provider.shutdown()


def test_new_sdk_provider_is_installed_once_and_reused(monkeypatch) -> None:
    proxy = ProxyTracerProvider()
    current = {"provider": proxy}
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://jaeger:4318/v1/traces")
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: current["provider"])
    monkeypatch.setattr(telemetry.trace, "set_tracer_provider", lambda provider: current.update(provider=provider))
    monkeypatch.setattr(telemetry, "OTLPSpanExporter", lambda **_: InMemorySpanExporter())

    provider = configure_telemetry("supportops-async-worker")
    assert isinstance(provider, TracerProvider)
    assert current["provider"] is provider
    assert configure_telemetry("supportops-async-worker") is provider
    assert shutdown_telemetry(provider)


def test_existing_provider_with_wrong_service_identity_is_not_modified(monkeypatch) -> None:
    provider = TracerProvider(resource=Resource({SERVICE_NAME: "unexpected-service"}))
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://jaeger:4318/v1/traces")
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: provider)
    exporter_calls = []
    monkeypatch.setattr(telemetry, "OTLPSpanExporter", lambda **kwargs: exporter_calls.append(kwargs))

    assert configure_telemetry("supportops-async-api") is None
    assert exporter_calls == []
    provider.shutdown()


def test_existing_provider_still_validates_endpoint_before_exporter_creation(monkeypatch) -> None:
    provider = TracerProvider(resource=Resource({SERVICE_NAME: "supportops-async-api"}))
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://user:password@jaeger:4318/v1/traces")
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: provider)
    exporter_calls = []
    monkeypatch.setattr(telemetry, "OTLPSpanExporter", lambda **kwargs: exporter_calls.append(kwargs))

    with pytest.raises(ValueError, match="invalid OTLP trace endpoint"):
        configure_telemetry("supportops-async-api")
    assert exporter_calls == []
    provider.shutdown()
