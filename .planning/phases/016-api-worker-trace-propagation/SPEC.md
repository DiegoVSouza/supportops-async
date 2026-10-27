# Phase 016 — API-to-worker trace propagation and safe failures

Status: PLANNED. Offline control implementation only; service trace export and RAG remain INCOMPLETE.

## Goal

Propagate W3C `traceparent` from the actual FastAPI task request through P04-owned SQS/Redis/in-memory broker messages, retries, and worker execution. Preserve context across the worker's step thread and after interruption/redelivery. Keep task failure state, outbox errors, and worker logs to fixed safe codes rather than exception text.

## Findings and constraints

- P04 owns a real FastAPI `/tasks` API, PostgreSQL/SQLite stores, SQS and Redis Streams broker adapters, worker process, idempotent effect ledger, and crash-recovery tests.
- P04 has no tracing instrumentation in source today. `opentelemetry-api==1.45.1` is present only transitively through FastAPI; declare the API dependency directly. This phase emits/propagates spans through the OTel API when a caller-configured provider exists, but does not add an exporter, endpoint, collector, Docker service, or bridge.
- Worker steps run in a manually created thread; context variables do not automatically cross that thread boundary. Copy the active context into the step thread.
- `Worker.process` currently stores `str(exc)` on the task and the API returns `task.error`; worker CLI also logs exception text and traceback. New failures must use fixed error codes.
- The project profile has `rag: false`. No retrieval runtime, owned knowledge source, tenant contract, or corpus exists. Do not create fixtures or import another project's sources to simulate RAG.
- Existing live campaign datasets/splits/rubrics, thresholds, API task schema, migrations, Docker stacks, historical evidence, and effect/idempotency contracts are protected.
- Paid budget is USD 0. No provider, credentials, external network, Docker, services, or effects are needed or permitted in this phase.

## Acceptance criteria

1. HTTP `traceparent` is parsed by the W3C propagator and the API's active span context is propagated only as a bounded `traceparent` field in the internal broker envelope. Baggage and arbitrary request headers are never copied.
2. SQS and Redis message serialization, retry/defer, redelivery, and dead-letter paths preserve trace context; old messages without context remain compatible.
3. Worker spans use the extracted parent context and pass it into the real threaded step runner. Tests cover API → broker → worker thread and retry/recovery after an interrupted/committed step without reapplying an effect.
4. Exception payload text does not enter newly persisted worker failure state, API task errors, outbox payloads, worker logs, or span exception events. Fixed operational error codes/status remain available.
5. Locked offline unit/fake gates pass. Full gate runs with Docker and Terraform absent from the child process PATH and no service endpoints configured; skipped service/build gates remain INCOMPLETE.
6. Historical artifacts, eval datasets/rubrics, campaign ledger, service configuration, and all pre-existing artifacts are byte-identical after validation.
7. RAG source integration and exported service traces remain clearly INCOMPLETE; this phase does not claim production trace delivery or live quality.

## Out of scope

RAG/retrieval, data ingestion, tenant authorization, new stores/migrations, exporter/collector endpoints, telemetry bridge/network setup, service lifecycle, Docker/Terraform execution, provider calls, prompt changes, live evaluation, campaign accounting, refund/effect changes, publication, push, or promotion.
