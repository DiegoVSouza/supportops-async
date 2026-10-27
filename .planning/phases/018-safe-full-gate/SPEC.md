# Phase 018: Safe full local acceptance gate

## Objective

Run P04's complete local offline and service acceptance gate, including the runtime image build and Terraform plan against phase-owned LocalStack, without overwriting historical test scratch data or touching another stack.

## Scope

- Make `scripts/check_full.py` require a fresh pytest base directory under `artifacts/evidence/`, so a full gate cannot clear an existing directory.
- Preserve prior scratch data at `artifacts/evidence/.pytest-tmp/` byte-for-byte.
- Commit the resulting source candidate before running the complete gate.
- Run with phase-owned PostgreSQL and LocalStack, locked dependencies, fake mode, no provider calls, and Terraform plan only.
- Capture commands, exit codes, sanitized outputs, candidate identity, Docker inventories, image digests, and cleanup.

## Constraints

- No provider/model calls, credentials, paid usage, deployment, Terraform apply, Redis/other shared service lifecycle, or changes to project datasets, rubrics, prompts, evaluation records, Compose, or Terraform source.
- Use a dedicated Compose project `p04-phase018-full-gate`, only PostgreSQL and LocalStack, configured ports 15432/14566 after availability checks.
- Docker build may pull publicly available build/runtime base images and locked packages; do not pass secrets or `.env` into the build. Stop if the build requests credentials or an unexpected external service.
- Terraform commands must use LocalStack at the phase-owned loopback endpoint. No AWS credentials except non-secret LocalStack placeholders inside the Terraform container.
- User, independent, dataset/rubric, and promotion reviews remain PENDING.
