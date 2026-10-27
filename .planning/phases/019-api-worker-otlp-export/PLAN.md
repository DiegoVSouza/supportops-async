# Phase 019 plan

## Ownership

Allowed write paths:

- `.planning/phases/019-api-worker-otlp-export/**`
- `pyproject.toml`
- `uv.lock`
- `scripts/check_full.py`
- `supportops_async/telemetry.py`
- `supportops_async/api/app.py`
- `supportops_async/api/runtime.py`
- `supportops_async/worker/cli.py`
- `tests/test_telemetry.py`
- `docs/harness/sources.lock.json`
- `artifacts/evidence/otlp-export-019/**`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/knowledge/P04-async.md`

Forbidden changes:

- Base Compose/Docker/Terraform files, datasets/splits/rubrics/graders/evaluation results/campaign ledgers, `.env*`, historical evidence outside phase 019, sibling source, root lab files, other Docker projects, and existing image tag `supportops-async:local-check`.
- Provider/model requests, customer data, cloud resources, image publication, deployment, Terraform apply, and changes to trace privacy policy or thresholds.

## Tasks

1. Add locked SDK/exporter packages, opt-in API/worker setup and bounded shutdown, image-tag parameter, focused tests, and official source/version records. Run offline fast/tests and commit candidate.
2. Build the unique candidate image, start a phase-owned Compose override with API/Redis/worker/PostgreSQL and Jaeger, send one synthetic API task, and assert correlated spans arrive in Jaeger.
3. Run the complete locked P04 gate with safe basetemp and unique image tag, clean only phase resources, reconcile Docker/history/image identities, review evidence/secrets, and record scoped status.

## Validation

- `uv run --locked python scripts/check_fast.py`
- `PYTHONPATH=. uv run --locked pytest -v --basetemp artifacts/evidence/otlp-export-019/offline-pytest tests`
- `P04_CHECK_IMAGE_TAG=supportops-async:phase019 P04_PYTEST_BASETEMP=artifacts/evidence/otlp-export-019/full-gate-pytest ... uv run --locked python scripts/check_full.py`
- `docker compose -p p04-phase019-otlp -f docker-compose.async.yml -f artifacts/evidence/otlp-export-019/compose.override.yml config --quiet`
- `docker compose -p p04-phase019-otlp -f docker-compose.async.yml -f artifacts/evidence/otlp-export-019/compose.override.yml up --pull never -d --wait`
- Run the phase service probe and require API/queue/worker/step spans with the same trace ID in Jaeger.
- `docker compose -p p04-phase019-otlp -f docker-compose.async.yml -f artifacts/evidence/otlp-export-019/compose.override.yml down --volumes --remove-orphans`
- `git diff --check` and staged-diff/secret review before commit.

## Budget and stop conditions

- Budget: USD 0; zero provider/model requests. Docker and Python package downloads are limited to the pinned public dependencies/base images required for this local runtime build; no credentials.
- Stop before startup if a port is occupied, required cached service image is absent, prior `.pytest-tmp` hashes changed, unique image tag already exists, phase namespace is nonempty, or a service config binds outside loopback.
- Stop on build/test/service failure, missing correlated trace, unexpected attributes/content, non-local route, any shared Docker state change, or uncertain cleanup. Record the real exit and do not retry a failed semantic workflow to obtain a pass.
- Commit/freeze source before service execution and do not alter the candidate afterward. Review gates remain PENDING.
