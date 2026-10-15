# Plan - Phase 007: LocalStack queue initialization

Plan fields:

project: p04
requirement_ids: [P04-007-001]
allowed_write_paths: [.planning/phases/007-localstack-init-fix/**, infra/localstack-init/**, infra/terraform/**, tests/integration/test_services.py, scripts/check_full.py, docker-compose.remediation.yml, .gitignore, artifacts/evidence/**, artifacts/tmp/**, docs/harness/**]
forbidden_changes: [sibling repositories, weakened tests, AWS deployment, Terraform apply, image publication, push, secrets]
dependencies:
  - Docker Compose 5.0.1, PostgreSQL 17.11-alpine3.24, LocalStack 4.14.0
  - AWS CLI syntax documented by AWS; source registered in docs/harness/sources.lock.json
llm_mode: fake
tasks:
  - Fix RedrivePolicy input for the current AWS CLI parser and validate the hook syntax.
  - Make service tests repeatable with unique PostgreSQL keys and a dedicated temporary SQS queue; make the full gate check the PostgreSQL host/port from its configured DSN instead of assuming port 5432.
  - Add a reproducible alternate-port Compose override, build/start the P04 API/worker images, verify health/non-root runtime, use local Terraform or the official pinned Docker image fallback for init/validate/plan, and commit the provider lock while ignoring generated .terraform data.
checks:
  - docker compose config and image build
  - uv run --locked pytest -q -m integration tests/integration/test_services.py
  - uv run --locked pytest -q
  - uv run --locked python scripts/check_full.py
stop_condition: Stop with any required service integration failure unresolved; mark absent executables INCOMPLETE and never infer PASS from a skipped test.

## Plan review
Coordinator review: accepted. The phase is restricted to P04 and local Docker evidence; all external effects are forbidden.

## Amendment after service execution
The first PostgreSQL service run passed, while the repeated run exposed a fixed idempotency key colliding with its persisted row. A full-suite run also showed the active worker can consume the fixed test message from the shared queue. The plan owns the integration test and full-gate script: tests use unique keys and a dedicated temporary queue, and reachability is checked at the configured PostgreSQL DSN. Existing same-key, SQS visibility, and acknowledgement assertions remain intact. Docker makes Terraform CLI available through the official versioned image, so this phase adds a Docker fallback for local init/validate/plan when the host CLI is absent; no apply is allowed. Coordinator review: accepted.

## Amendments for repeatable local Docker use
The host already has other Compose stacks bound to 5432, 4566, and 6379. The phase adds a committed P04-only alternate-port override rather than stopping unrelated containers. Terraform init generated a provider lock; the lock is source-controlled while generated .terraform plugin data is ignored. Coordinator review: accepted.
