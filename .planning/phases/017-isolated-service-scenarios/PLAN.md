# Phase 017 plan

## Ownership

Allowed write paths:

- `.planning/phases/017-isolated-service-scenarios/**`
- `artifacts/evidence/service-scenarios-017/**`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/knowledge/P04-async.md`

Forbidden changes:

- Product/runtime source, dependencies, locks, datasets, rubrics, prompts, Compose/Terraform definitions, prior evidence, and any other project's files.
- Any existing Docker resource not labeled with this phase's Compose project.
- Provider access, secrets, image builds/pulls, cloud actions, and paid usage.

## Tasks

1. Confirm scenario contract, phase identity, cached image digests, empty phase namespace, and free ports; capture pre-run Docker inventory and locked offline checks.
2. Run the existing real PostgreSQL/SQS scenario using isolated PostgreSQL and LocalStack containers, then reconcile results and capture post-run inventory.
3. Clean up only the isolated project, review evidence/diff for secrets and scope, and record scoped gate status.

## Validation commands

- `uv run --locked python scripts/check_fast.py`
- `uv run --locked pytest -q --basetemp artifacts/evidence/service-scenarios-017/pytest-tmp`
- `docker compose -p p04-phase017-isolated-service -f docker-compose.async.yml up --pull never --no-build -d --wait postgres localstack`
- `uv run --locked python scripts/service_scenarios.py`
- `docker compose -p p04-phase017-isolated-service -f docker-compose.async.yml down --volumes --remove-orphans`
- `git diff --check` and staged-diff/secret review before commit.

## Budget and stop conditions

- Budget: USD 0; zero provider calls; cached local images only; no image build/pull.
- Stop before startup if either port is occupied, image digest differs/is absent, project namespace is nonempty, or Compose would build/pull or target shared resources.
- Stop on any unexpected container/network/volume identity change, scenario failure, provider/credential discovery, or uncertain cleanup. Preserve evidence and report INCOMPLETE; do not rerun a failed semantic case to obtain a pass.
- Required personal, independent, dataset/rubric, and promotion reviews remain PENDING.
