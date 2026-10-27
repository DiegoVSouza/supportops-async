# Phase 019: Export API and worker traces over OTLP

## Objective

Connect P04's existing W3C API-to-queue-to-worker spans to a configurable OTLP exporter and verify the real Compose API/Redis/worker path in a phase-owned Jaeger instance.

## Scope

- Add pinned OpenTelemetry SDK and OTLP HTTP exporter packages compatible with the existing API version.
- Configure opt-in, privacy-bounded exporter lifecycle in the real API and worker processes; retain no-op behavior when the endpoint is unset.
- Preserve current trace context, error-category allowlist, and `record_exception=False` behavior.
- Parameterize the full-gate image tag so phase 019 builds a unique P04 image instead of replacing `supportops-async:local-check`.
- Use a phase-owned Compose override and service probe to confirm one trace links API, queue publish, worker processing, and step execution in Jaeger.

## Constraints

- No LLM/provider call, credentials, paid usage, customer data, dataset/rubric/evaluation changes, Terraform apply, public listener, or changes to base Compose files.
- Use only P04's actual API, Redis, worker and PostgreSQL services, plus a local Jaeger container on the same isolated network. Host ports must bind loopback and be checked free.
- No sibling project source imports. OTLP endpoint configuration must reject userinfo, query, and fragment; spans must not include prompts, payloads, exception messages, or traceback.
- Keep previous image tag, service stacks, historical artifact/eval files, and P00/P01 work intact.
- Human/independent/dataset/rubric/promotion reviews remain PENDING.
