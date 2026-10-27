# Plan — API-to-worker trace propagation and safe failures

## Execution controls

- `llm_mode`: `fake`; use OTel API with in-process context only. No SDK exporter, provider, credentials, `.env`, network, Docker daemon, services, or external effects.
- `allowed_write_paths`:
  - `.planning/phases/016-api-worker-trace-propagation/**`
  - `supportops_async/tracing.py`
  - `supportops_async/api/app.py`
  - `supportops_async/queue/contracts.py`
  - `supportops_async/queue/memory.py`
  - `supportops_async/worker/runner.py`
  - `supportops_async/worker/cli.py`
  - `pyproject.toml`
  - `uv.lock`
  - `tests/api/test_tasks_api.py`
  - `tests/queue/test_broker.py`
  - `tests/worker/test_worker.py`
  - `tests/recovery/test_process_recovery.py`
  - `docs/architecture.md`
  - `docs/harness/progress.md`
  - `docs/harness/failures.md`
  - `docs/harness/feature_list.json`
  - `docs/knowledge/P04-async.md`
  - `artifacts/evidence/api-worker-trace-propagation/**`
- `forbidden_changes`: API request/task payload schema, effect keys/semantics, DB migrations/stores, retry limits, broker durability semantics, frozen datasets/rubrics/campaign config/ledger, historical live evidence, `.env*`, Docker/Compose/Terraform config, `scripts/check_full.py`, other projects, root lab/harness-kit, RAG corpus/connectors, telemetry exporter/endpoint, provider/network/service calls, paid spend, deployment, refund/customer effects, publication, push, or weakened tests.
- Budget: zero provider calls/tokens, USD 0, no external network. Local CPU only.
- Validation commands: focused locked pytest for API, brokers, worker, and process recovery; `uv lock --check`; fast gate; full gate under `P04_SKIP_SERVICES=1` with PostgreSQL/LocalStack environment unset and Docker/Terraform removed from subprocess `PATH`. Snapshot and restore any full-gate artifacts outside this phase evidence. Save exact commands, exits, outputs, and hash comparisons.
- Stop conditions: if a correctness proof requires live SQS/Redis/PostgreSQL/Docker, an exporter/collector, a new DB migration, provider request, RAG source, or changed evaluation protocol, leave that dependent gate INCOMPLETE and produce a concrete proposal without contacting the service.

## Tasks

1. **Test trace context and failure privacy first** — add regressions for validated W3C parent extraction, API broker envelope, SQS/Redis serialization and retry preservation, worker thread context, crash recovery without duplicate effects, and safe persisted/logged error codes.
2. **Implement API-owned propagation and safe error reporting** — add direct pinned OTel API dependency and P04 tracing helper, instrument API/worker boundaries, propagate only `traceparent` through broker messages, carry context into the worker step thread, and replace exception text with fixed error codes.
3. **Verify isolated runtime contracts and document incomplete integrations** — run focused/fast/full offline checks with Docker/Terraform hidden, compare historical artifacts/datasets/configs before and after, update phase/project docs, inspect staged paths/secrets, and commit locally.

## Plan check

Implementer self-check against P04's API, queue/store/worker implementation, phases 013–015, project profile, and campaign privacy/zero-budget decisions. Existing numeric IDs were inspected across `.planning/phases/` and `docs/harness/phases/`; phase 016 is the next unused ID. RAG is not enabled and has no P04-owned source, so it stays INCOMPLETE. No exporter/bridge or service lifecycle is included. Independent review remains PENDING.
