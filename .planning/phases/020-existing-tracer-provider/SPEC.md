# Phase 020: Configure OTLP with an existing SDK provider

## Objective

Fix API OTLP startup so spans export even when a `TracerProvider` was installed before FastAPI lifespan startup. Diagnose the owner and resource identity of the existing provider, avoid replacing a global provider, and preserve the phase-019 failed task and trace as immutable history.

## Scope

- Correct `configure_telemetry` to adopt and instrument an existing SDK `TracerProvider` safely, while retaining opt-in behavior and no-op behavior when no endpoint is configured.
- Make configuration idempotent within a process and reject or safely report incompatible provider service identity without exporting payload/error content.
- Add offline tests for proxy-provider setup, preconfigured SDK provider setup, repeated setup, service/resource attribution, unsafe endpoints, shutdown/flush behavior, and worker/API lifecycle.
- Freeze a new candidate commit before one new synthetic local API-to-worker Jaeger probe. The probe must use a new idempotency key and trace ID; do not replay phase-019's task or trace.
- Run locked fast/offline checks and the full local gate only after the correlated API and worker spans are proven. Preserve the phase-019 image tag and all prior evidence.

## Constraints

- No provider/model requests, credentials, paid calls, cloud effects, Terraform apply, public listeners, eval/dataset/rubric changes, or changes to trace payload/privacy policy.
- Preserve task `ac52c679-8226-4658-9eca-6739e4caf906`, trace `4bf92f3577b34da6a3ce929d0e0e4736`, and phase-019 failure evidence. The one-shot phase-019 probe may not be rerun.
- Use a new unique image tag and a phase-owned Compose namespace. Only loopback host bindings are allowed. Stop if unrelated Docker inventory changes or cleanup is uncertain.
- All human/release reviews remain PENDING; a local service trace is not a quality or promotion result.
