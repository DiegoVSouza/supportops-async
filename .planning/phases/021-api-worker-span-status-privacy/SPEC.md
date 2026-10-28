# Phase 021 — Keep API and worker error status content-free

## Goal

Close a privacy gap in P04's actual API middleware and worker process spans: OpenTelemetry can copy exception messages into span ERROR status descriptions even when exception events are disabled.

## Acceptance criteria

1. Add red-first in-memory SDK exporter tests for exceptions escaping both the actual FastAPI request middleware and worker `process` span; a unique sentinel must be absent from status description, events and attributes.
2. Preserve fixed `supportops.error.category`, generic ERROR status, request/worker behavior and propagation of the original exception to its caller.
3. Disable only OpenTelemetry's automatic exception status mutation on P04's API and worker outer spans. Do not change traces, propagation, stores, brokers, retries, API contracts or telemetry exporter setup.
4. Run focused, fast and offline full gates in fake mode; if service dependencies are unavailable, retain accurate INCOMPLETE status. No provider calls, credentials, Docker lifecycle or external systems.
5. Update P04 verification/progress/failures/features/knowledge, record exact evidence, scan staged files for secrets and commit locally.

## Scope limits

This proves only the tested SDK/in-memory API and worker span behavior, not production collector retention or external exporters. Human, independent, model-quality, billing and promotion reviews remain pending.
