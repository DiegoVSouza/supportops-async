# Progress

- Kit initialization and intake completed; the project profile and module lock are recorded.

## 2026-10-15 — Intake and plan review

- Original acceptance criteria were reconciled into four local phases, each with SPEC, PLAN, and VERIFY before product code.
- Plan review accepted; every PLAN declares allowed paths, forbidden changes, 2–4 observable tasks, validation, and stop conditions.
- Dependencies are pinned in `uv.lock`; current official sources and checked versions are in `docs/harness/sources.lock.json`.
- Phase 001 API and SQLite store behavior, phase 002 broker/worker behavior, and phase 003 SQLite subprocess recovery/outbox behavior have unit evidence.
- Phase 004 source files and local demo are implemented. Compose configuration validation passes.
- Package `supportops-async` v0.1.0 and v0.1.1 wheels were committed locally with provenance; remediation release 0.1.2 adds long-step lease renewal and is recorded in `artifacts/packages/provenance-0.1.2.md`.
- PostgreSQL and LocalStack integration, Docker image build, and Terraform validation/plan are INCOMPLETE because the services/daemon/CLI are unavailable.
- Full dependency resolution in a fresh offline venv is INCOMPLETE because the uv offline resolver could not source `psycopg-binary`; the wheel-only install and smoke with the project's locked installed dependencies passed.
- LLM mode remains fake; model quality and cost metrics are PENDING.

## 2026-10-15 — Lease renewal remediation

- Worker now renews the task-store lease and broker visibility on a configurable interval while a step runs. Local long-step tests prove renewal and reject a competing worker claim; evidence: `artifacts/evidence/phase-006-unit-suite.txt` (27 passed, 2 skipped).
- Compose configuration passes. The required full gate exits 2/INCOMPLETE because PostgreSQL, LocalStack, Docker daemon, and Terraform CLI are unavailable; see `artifacts/evidence/phase-006-full-gate.txt`.
- Service-backed recovery, image build, Terraform validation/plan, and end-to-end service behavior remain INCOMPLETE. Model quality and cost remain PENDING.

## 2026-10-15 — FastAPI consumer compatibility

- P05's FastAPI 0.142.4 pin was tested in an isolated compatibility environment: API contract 2/2 and all 25 local unit/recovery tests passed.
- ADR-001 sets the tested range to `>=0.137.1,<0.143.0`; the new lock resolves FastAPI 0.142.4 and OpenTelemetry API 1.45.1. Full local tests pass on both range endpoints. P04 does not configure telemetry exporters.
- The API and public task contract did not change. The 0.1.2 wheel was built offline and passed isolated consumer smoke; full offline dependency recreation remains INCOMPLETE because `psycopg-binary` is absent from the cache.

## 2026-10-15 - Docker service verification

- Phase 007 fixed the LocalStack READY hook to pass SQS RedrivePolicy as a JSON map file, as required by AWS CLI 1.44.45. P04 service tests now use unique PostgreSQL idempotency keys and a temporary SQS queue so they can repeat with a persistent database and a running worker.
- The PostgreSQL/LocalStack integration test passed twice (2 tests each run). The full suite passed with services configured (29 passed), and a Docker API/worker task completed and persisted as status done; both containers run as UID 10001. Evidence: artifacts/evidence/phase-007-service-tests-repeat-1.txt, phase-007-service-tests-repeat-2.txt, phase-007-full-tests.txt, and phase-007-docker-demo.txt.
- python scripts/check_full.py passes with PostgreSQL/LocalStack configured. It validates Compose, builds the non-root image, runs tests, and uses the official Terraform 1.16.6 Docker image for init, validate, and a local-only plan (6 resources to add, 0 to change/destroy). Evidence: artifacts/evidence/phase-007-check-full.txt. No Terraform apply was run.
- A test with a step longer than the lease interval against PostgreSQL and SQS, full crash/retry/DLQ recovery against services, and cloud deployment remain INCOMPLETE. Model quality and cost remain PENDING.
