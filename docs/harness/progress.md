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

## 2026-10-21 — PostgreSQL and LocalStack service scenarios

- Phase 008 reran the full local gate successfully: 29 tests, Compose configuration, image build, and Terraform 1.16.6 init/validate/plan against LocalStack (6 resources to add, no changes or destroys; no apply). Evidence: `artifacts/evidence/phase-008-full-gate-rerun-summary.txt` and full output `phase-008-full-gate-rerun.txt`.
- PostgreSQL/SQS long-step scenario passed after 31.7 seconds; the PostgreSQL lease and SQS visibility heartbeat prevented a competing claim and persisted task completion. Duplicate delivery produced one effect record. Retry exhaustion reached attempt 3 and placed one message in the DLQ. Evidence: `artifacts/evidence/phase-008-service-scenarios.txt`; service integration tests: `phase-008-service-tests.txt`.
- Service crash after a committed external effect remains INCOMPLETE. The effect ledger is not a universal exactly-once guarantee. Model quality and cost remain PENDING.

## 2026-10-22 — Service crash recovery

Phase 009 kills a subprocess after its PostgreSQL effect commit, waits for the actual 30-second lease and recovers via real SQS. The first effect is skipped, only the remaining step executes, and one effect row persists. Full gate exit 0: 30 tests plus long-step, duplicate, retry/DLQ, image and Terraform plan. Follow-up phase 010 will fix early redelivery during an unexpired store lease: the current worker acknowledges a failed claim and may discard recoverable work.

## 2026-10-23 — Phase 012 Redis Streams runtime

The API and worker now accept the shared Redis Streams broker while retaining the SQS adapter. Consumer groups reclaim abandoned work after the visibility timeout; failed work moves atomically to a delayed sorted set and is promoted for retry, while exhausted work uses a separate DLQ stream. The existing PostgreSQL lease and effect ledger remain authoritative. Local Compose uses persistent Redis AOF and loopback-only host ports. The full gate passed with 32 tests, PostgreSQL/SQS legacy scenarios, Redis retry/recovery/DLQ, image build, and Terraform init/validate/plan only; evidence is `artifacts/evidence/phase-012-full-gate.txt`. Wheel 0.1.4 and P05 consumer provenance are pending.

P04 0.1.4 was built from source commit `f4b5df828b397e7ecbb9fa87c0ef77485d829dca`. The wheel SHA-256 is `fefb871993591cabe7f9baba132e9f430ddbd65dd730c6789e22dc86d4d87c3f`; its locked dependencies and isolated consumer smoke passed. P05 provenance is the next consumer update.

## 2026-10-22 — Early-redelivery fix, 0.1.3

A failed store claim now defers the broker message instead of acknowledging it. Retry caps count actual store execution attempts rather than broker receive counts inflated by lease contention. The regression failed before and passed after; real subprocess recovery now attempts early SQS redelivery while the PostgreSQL lease remains active, then recovers after its actual expiry with one effect row. Full gate passed with 31 tests and existing service scenarios. Wheel provenance checks use the dependency lock at the artifact source commit, while current source lock consistency is checked separately. Patch wheel construction follows this source commit.

## 2026-10-22 — phase 010 completed

The phase 010 regression fixed early SQS redelivery during an active PostgreSQL lease. Failed claims defer the message; retry limits count actual task execution claims. A process killed after a committed PostgreSQL effect recovered over LocalStack SQS after lease expiry without repeating the first effect. P04 0.1.3 wheel and consumer smoke passed. The earlier phase 009 note that the follow-up fix remained pending is historical and superseded by phase 010. No Terraform apply or external effect was run.


## 2026-10-22 - phase 011 offline dependency recreation

All 34 locked project and development packages were installed into a fresh temporary Python 3.13 environment with `uv sync --offline --locked --all-groups`; the P04 fast gate passed from that environment with offline/no-sync mode. Evidence: `artifacts/evidence/phase-011-offline-dependencies.txt`. This verifies the current machine's populated uv cache, not a cold-cache or arbitrary-machine install. The earlier phase 010 failure was a service-availability failure (missing PostgreSQL DSN), not an offline resolver failure.

## 2026-10-26 — Phase 013 live workflow planning

- Added the optional Groq planner for one synthetic policy question; JSON output is validated against the local two-step allowlist before entering SQLite + memory broker + worker.
- Four numbered credentials passed preflight. The real run completed `triage` and `draft_reply` with one effect each (120 input / 25 output tokens). Cost remains `PENDING` under free-plan billing uncertainty.
- Offline focused tests passed (7), and full test suite passed (35; 4 external-service tests skipped). Overall service gate is incomplete only because PostgreSQL, LocalStack, Docker, and Terraform are not configured.

## 2026-10-26 — Live evaluation readability cleanup

- Separate model generation from local worker execution and artifact writing; compare the boolean checks directly with all(checks.values()).
- Full offline gate: INCOMPLETE (35 tests pass, 4 external-service tests skipped; PostgreSQL, LocalStack, Docker and Terraform prerequisites unavailable).
- Offline helper and static checks passed; no live calls were needed. Evidence: artifacts/evidence/code-cleanup/.
