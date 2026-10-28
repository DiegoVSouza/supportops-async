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

## 2026-10-26 — Live Docker acceptance

The full Docker/PostgreSQL/SQS/Redis/Terraform gate passed. The first real workflow reached both provider steps but failed the reply output contract (488 input / 203 output tokens); its evidence is retained. The prompt now states explicit JSON key schemas. One corrective workflow passed with a real plan and two real worker calls (526 input / 195 output tokens), two persisted effects and no regeneration on duplicate delivery. Eight focused tests include rejection of missing, empty and non-object outputs. Evidence: artifacts/evidence/live-docker/.

## 2026-10-27 — Phase 021 API/worker span status privacy

- Red-first in-memory exporter tests on the actual API middleware and worker process spans reproduced automatic exception-message insertion into ERROR status descriptions, despite `record_exception=False`.
- Both outer spans now pass `set_status_on_exception=False`; the existing fixed category and generic ERROR status remain, and the original exception reaches the caller. Focused suite passed 15 tests; fast check passed.
- Full offline gate passed 82 tests with four expected service integration skips, Compose config passed, and returned INCOMPLETE because PostgreSQL, LocalStack, Docker build and Terraform prerequisites were unavailable/explicitly disabled. No provider, credentials, network or Docker lifecycle was used.
- This closes only the local SDK/in-memory privacy contract. Production OTLP privacy/delivery, quality, billing, human/independent review and promotion remain INCOMPLETE/PENDING. Evidence: `artifacts/evidence/api-worker-span-privacy-021/`.
## 2026-10-26 — Phase 012 bounded campaign ledger

- Added P04-local append-only reservations, atomic cumulative caps, a process lease, and read-only resume inspection. Unknown usage remains fully reserved and cannot be replayed.
- Focused tests passed: 6 ledger and 11 preparation tests. Full gate passed 60 tests with 4 service skips and returned `INCOMPLETE` because PostgreSQL/LocalStack/Redis/Docker build/Terraform validation were isolated. Compose config passed.
- Dispatcher, service recovery validation, authorized quota/caps, reviewer approval, live-path lease integration, canary, and rollback remain pending. No provider call or workflow effect occurred. Evidence: `artifacts/evidence/live-campaign-ledger/`.

## 2026-10-27 — Phase 016 API and worker trace propagation

- Added W3C trace context propagation from the real FastAPI request into SQS/Redis/in-memory broker envelopes, retry/defer and DLQ fields, worker processing spans, and the step execution thread. Legacy messages without `traceparent` remain accepted.
- Worker failure state, outbox error fields, and CLI iteration logs now use fixed error categories and omit exception text. Trace spans disable exception recording and carry only bounded method/status/attempt/category attributes.
- Focused locked tests: 20 passed, including API-to-broker propagation, legacy and retry/DLQ queue messages, worker thread context, private exception text exclusion, and crash recovery without repeating a committed effect.
- Fast gate passed. Offline full gate: 67 passed and 4 service tests skipped; overall INCOMPLETE because PostgreSQL, LocalStack, Docker build, and Terraform were unavailable. Compose config passed. No SDK exporter, collector, RAG source, provider, Docker daemon, or external service was configured or accessed. Service trace delivery and RAG stay INCOMPLETE. Protected artifact/eval/config hash comparison reported zero changes.

## 2026-10-27 — Phase 017 isolated service scenario recheck

- Rechecked the unchanged phase-016 source candidate against isolated PostgreSQL 17.11 and LocalStack 4.14.0 using cached images and a dedicated Compose project. Long-step lease renewal completed in 31.8 seconds without a competing claim and persisted the effect; duplicate delivery recorded one claim/effect; three retries reached failed state with exactly one DLQ message.
- Fast gate passed; offline suite passed 67 tests with 4 expected service skips when service environment was absent. Isolated service scenarios passed. Docker reconciliation: 102 existing containers, 21 networks, and 89 volumes were preserved after the two phase containers, one network, and one volume were removed.
- The first invocation exposed that Compose binds Postgres/LocalStack on 15432/14566, not the initially planned 16432/16566. That invocation made no application DB/SQS requests and was interrupted; the phase plan was corrected before the successful run. No provider was accessed. Evidence: `artifacts/evidence/service-scenarios-017/`.
- This does not demonstrate API/worker trace export, RAG, Docker image build, Terraform, model quality, or promotion. Those gates and all human reviews remain INCOMPLETE/PENDING.

## 2026-10-27 — Phase 018 safe full local gate

- Updated `scripts/check_full.py` to require a new pytest scratch directory under `artifacts/evidence/` and refuse to clear a pre-existing path. It safely refused the historical `.pytest-tmp` before running other checks; a fresh phase directory passed.
- Candidate `ee8c867b824b7727f547dd01b07275b179687add` passed `check-full.py` with isolated PostgreSQL/LocalStack: 70 passed, 1 Redis test skipped because no Redis endpoint was configured; service long-step/duplicate/retry-DLQ scenarios passed; Docker image build passed; Terraform init/validate passed; local LocalStack plan was 6 add, 0 change, 0 destroy (no apply). Full gate exit 0.
- Historical `.pytest-tmp` three-file hashes stayed unchanged. Pre-existing container IDs, normalized states, image references, networks, and volumes were unchanged; phase containers/network/volume were removed. The planned build replaced the existing P04-owned `supportops-async:local-check` image tag (old image ID recorded, new image ID recorded); other service stacks were untouched. Evidence: `artifacts/evidence/full-gate-018/`.
- The gate does not validate Redis service behavior, API trace export delivery, RAG, model quality, human/independent review, or promotion. Those remain INCOMPLETE/PENDING.

## 2026-10-27 — Phase 019 OTLP exporter attempt

Candidate `d6cf5c9039e5dfd746331fda3f192e66e6e67184` passed the fast gate and 75 offline tests (4 expected service skips); unique image build and isolated Compose startup passed. The single synthetic local request completed, but Jaeger returned only the worker span and the API logged `Overriding of current TracerProvider is not allowed`. The API+worker export gate is FAIL and phase 019 remains INCOMPLETE. The task UUID and deterministic trace ID are preserved under `artifacts/evidence/otlp-export-019/`; do not replay this probe. Phase-owned containers, network, and volumes were removed; the prior `supportops-async:local-check` tag remains unchanged. No provider/model request occurred.

## 2026-10-27 — Phase 020 existing-provider OTLP fix

Candidate `beff749202805b138d820daaddb80a4468afc7c9` passed 13 focused telemetry tests, the fast gate, and the full offline suite (80 passed, 4 expected service skips). One new synthetic local request completed; Jaeger GET-only readback found six same-trace spans including API request and worker processing, correct API/worker service names, scalar allowlisted keys, and no UUID-shaped attribute values. The submit verifier itself exited 1 on a Python dict/set bug after task completion; no request replay occurred and the GET-only readback passed. Full gate passed with 84 tests, real service lease/duplicate/retry-DLQ scenarios, Docker image build, Terraform init/validate and a LocalStack plan (6 add, 0 change, 0 destroy; no apply). Exit 0. Phase namespace teardown returned exact Docker baseline: 102 containers, 21 networks, 89 volumes. No model/provider request. Phase 019's failed event remains historical; current OTLP export gate passes on phase 020. Evidence: `artifacts/evidence/otel-provider-020/`.

## 2026-10-28 - Phase 022 current service scenarios

- Isolated PostgreSQL, LocalStack and Redis integration tests and long-step, duplicate and retry/DLQ scenarios passed. Docker inventories reconciled. The complete Terraform gate and current exporter privacy remain incomplete; evidence: artifacts/evidence/current-service-scenarios-022/.
