# Phase 018 — Safe full local acceptance gate

Date: 2026-10-27

## Candidate and implementation

Candidate commit: `ee8c867b824b7727f547dd01b07275b179687add` (`fix(harness): protect full-gate test scratch`). It adds a configurable pytest base directory to `scripts/check_full.py`, requires that it resolve under `artifacts/evidence/`, refuses existing/symlinked paths, and creates a fresh path before invoking pytest. No runtime/model source, dependencies, locks, dataset, rubric, prompts, Compose/Terraform source, or evaluation records changed during this phase.

The previous default `artifacts/evidence/.pytest-tmp/` existed and contained three SQLite files. Guard test with that existing path exited 1 before any gate work. Guard test with `../outside-evidence` also exited 1. The prior three files' SHA-256, paths, and lengths match before and after.

## Full gate

Command: `P04_PYTEST_BASETEMP=artifacts/evidence/full-gate-018/full-gate-pytest P04_POSTGRES_DSN=<phase-local> P04_LOCALSTACK_ENDPOINT=<phase-local> LLM_MODE=fake PYTHONPATH=. uv run --locked python scripts/check_full.py`

Exit: 0, `check-full: PASS`.

- Fast gate: exit 0.
- Service-enabled suite: exit 0; 70 passed, 1 skipped (`tests/queue/test_redis_broker.py`) because `P04_TEST_REDIS_URL` was not configured.
- Compose config: exit 0.
- PostgreSQL/SQS long-step, duplicate-delivery, and retry/DLQ scenarios: exit 0.
- Docker image build: exit 0.
- Terraform 1.16.6 init and validate: exit 0.
- Terraform plan against `http://host.docker.internal:14566` (phase-owned LocalStack): exit 0; 6 to add, 0 to change, 0 to destroy. No apply.
- Runtime mode was fake. No LLM provider/model endpoint was contacted. Terraform used only placeholder LocalStack credentials.

## Local resource reconciliation

The dedicated Compose namespace `p04-phase018-full-gate` was stopped and removed with `down --volumes --remove-orphans`. No phase containers remain. Before/after: 102 containers, 21 networks, 89 volumes; all pre-existing container IDs, normalized states, referenced images, network identities, and volume names match. The three historical pytest scratch hashes match.

The requested project image build replaced the existing P04 tag `supportops-async:local-check`: pre-build short ID `d7ff4a414ee2` (the full digest was not captured), new ID `sha256:5cc87bb6e992903af9b4a5dfa2c6e4a14a2d6d6a28f8a7fa37dfc34c8354e505`. This tag is owned by P04; no running container referenced it, and no pre-existing service identity/state changed. The new tag remains available as the locally built candidate image.

## Remaining gates

The P04 full script reports PASS, with Redis service-backed tests skipped. Broader acceptance remains INCOMPLETE for Redis live service validation, API trace exporter delivery, RAG/product-level acceptance, model quality, and review/promotion. User, independent, dataset/rubric, and promotion reviews remain PENDING.

Full command output, exits, inventories, protected scratch hashes, guard outputs, and SHA-256 manifest are in this directory. No secrets or model responses are present.
