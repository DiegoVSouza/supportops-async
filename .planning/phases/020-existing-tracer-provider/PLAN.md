# Phase 020 plan

## Ownership

Allowed write paths:

- `.planning/phases/020-existing-tracer-provider/**`
- `supportops_async/telemetry.py`
- `tests/test_telemetry.py`
- `scripts/check_full.py`
- `artifacts/evidence/otel-provider-020/**`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/knowledge/P04-async.md`

Forbidden changes:

- Phase-019 source/evidence, prior historical artifacts, source datasets/splits/rubrics/graders/evaluation campaigns, `.env*`, Dockerfile/base Compose/Terraform files, sibling projects, root harness/kit, old image tags, provider/model requests, credentials, paid use, cloud changes, deploy, public listeners, Terraform apply, or non-phase Docker stacks.

## Tasks

1. Diagnose the provider already present at API startup using type-only diagnostics. Add unit tests for provider installation/adoption, repeated setup, service identity, endpoint rejection, and shutdown; implement idempotent exporter attachment without replacing global state. Run fast and complete offline tests; commit the candidate.
2. Build a new unique image and use a phase-owned service stack. Submit exactly one new synthetic task with a new trace ID/key; require API request, queue/worker processing, and step spans in Jaeger with matching trace IDs and only allowlisted attributes. Do not replay phase 019's request.
3. After the service probe passes, run full locked checks with an evidence-owned basetemp and the unique image tag; reconcile Docker resources, artifacts, previous image tags, and privacy; update docs and commit evidence. If the service probe fails, stop, record FAIL/INCOMPLETE, clean only phase resources, and do not rerun.

## Validation

- `uv run --locked python scripts/check_fast.py`
- `PYTHONPATH=. uv run --locked pytest -v --basetemp artifacts/evidence/otel-provider-020/offline-pytest tests`
- `docker compose -p p04-phase020-otel -f docker-compose.async.yml -f artifacts/evidence/otel-provider-020/compose.override.yml config --quiet`
- Build candidate tag `supportops-async:phase020` after confirming it is absent.
- One service probe using the new phase-owned stack and an evidence-owned one-shot marker.
- On probe pass only: `P04_CHECK_IMAGE_TAG=supportops-async:phase020 P04_PYTEST_BASETEMP=artifacts/evidence/otel-provider-020/full-gate-pytest PYTHONPATH=. uv run --locked python scripts/check_full.py`
- Reconcile phase namespace and inventory; `git diff --check`; staged diff and secret review.

## Budget and stop conditions

- Budget: USD 0; zero provider/model calls, no credentials, no external/cloud effects. Local synthetic API task and cached/local Compose services only.
- Stop before startup if ports are occupied, image tag/project namespace exists, required cached images are absent, Compose binds outside loopback, or historical evidence/image identity differs.
- Stop on provider collision, incorrect resource/service attribution, API span missing, trace mismatch, unexpected span content, test/build/service failure, unrelated resource change, or uncertain cleanup. Record exact output and do not repeat the semantic service probe.
- Preserve phase-019 outcome; no independent review, dataset/rubric approval, or human promotion approval is inferred.
