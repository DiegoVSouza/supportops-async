# Phase 018 plan

## Ownership

Allowed write paths:

- `.planning/phases/018-safe-full-gate/**`
- `scripts/check_full.py`
- `artifacts/evidence/full-gate-018/**`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/knowledge/P04-async.md`

Forbidden changes:

- Runtime/product source outside `scripts/check_full.py`, dependencies/lock, datasets, rubrics, prompts, evaluation manifests/results, Compose/Terraform source, and prior evidence.
- Existing `.pytest-tmp` files, any Docker resource outside the phase project, other projects, and any external cloud resource.
- Provider/model calls, Terraform apply, deploy, paid use, secret access, or public listener.

## Tasks

1. Add a safe configurable pytest base directory to the full gate; reject existing paths and paths outside project evidence. Validate the guard, fast checks, and offline suite; commit the candidate.
2. Start only phase-owned PostgreSQL/LocalStack and run the full gate with a fresh evidence-owned pytest directory, fake mode, and LocalStack Terraform plan.
3. Reconcile Docker resources and protected scratch hashes, clean only the phase stack, review staged paths and secrets, and record scoped gate status.

## Validation commands

- `uv run --locked python scripts/check_fast.py`
- `PYTHONPATH=. uv run --locked pytest -q -rs --basetemp artifacts/evidence/full-gate-018/offline-pytest tests`
- `P04_PYTEST_BASETEMP=artifacts/evidence/.pytest-tmp uv run --locked python scripts/check_full.py` (expected safe refusal before tests or service changes)
- `P04_PYTEST_BASETEMP=artifacts/evidence/full-gate-018/full-gate-pytest P04_POSTGRES_DSN=... P04_LOCALSTACK_ENDPOINT=... LLM_MODE=fake PYTHONPATH=. uv run --locked python scripts/check_full.py`
- `docker compose -p p04-phase018-full-gate -f docker-compose.async.yml down --volumes --remove-orphans`
- `git diff --check` and staged-diff/secret review before commit.

## Budget and stop conditions

- Budget: USD 0; zero model/provider calls; Terraform plan only against LocalStack. Docker base image/package downloads are allowed only as part of the local image build.
- Stop before startup if ports are occupied, cache/source identity differs, old pytest scratch hashes differ, phase project namespace is nonempty, or a command would pull an unexpected image or affect a shared stack.
- Stop on build/plan failure, evidence of non-local cloud routing, secret exposure, or cleanup uncertainty. Record exact failure and keep gate FAIL/INCOMPLETE; do not retry semantic scenarios to manufacture a pass.
- Do not edit the candidate after the gate starts. User, independent, dataset/rubric, and promotion reviews remain PENDING.
