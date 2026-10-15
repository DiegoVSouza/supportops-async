# Plan - Phase 007: LocalStack queue initialization

Plan fields:

project: p04
requirement_ids: [P04-007-001]
allowed_write_paths: [.planning/phases/007-localstack-init-fix/**, infra/localstack-init/**, tests/integration/test_services.py, artifacts/evidence/**, docs/harness/**]
forbidden_changes: [sibling repositories, weakened tests, AWS deployment, Terraform apply, image publication, push, secrets]
dependencies:
  - Docker Compose 5.0.1, PostgreSQL 17.11-alpine3.24, LocalStack 4.14.0
  - AWS CLI syntax documented by AWS; source registered in docs/harness/sources.lock.json
llm_mode: fake
tasks:
  - Fix RedrivePolicy input for the current AWS CLI parser and validate the hook syntax.
  - Make the PostgreSQL idempotency fixture unique per invocation and use a dedicated temporary SQS queue so the running worker cannot consume the test message; re-run service tests against isolated Compose.
  - Build and start the P04 API/worker images, verify health/non-root runtime, then run the project full gate and record unavailable Terraform checks.
checks:
  - docker compose config and image build
  - uv run --locked pytest -q -m integration tests/integration/test_services.py
  - uv run --locked pytest -q
  - uv run --locked python scripts/check_full.py
stop_condition: Stop with any required service integration failure unresolved; mark absent executables INCOMPLETE and never infer PASS from a skipped test.

## Plan review
Coordinator review: accepted. The phase is restricted to P04 and local Docker evidence; all external effects are forbidden.

## Amendment after service execution
The first PostgreSQL service run passed, while the repeated run exposed a fixed idempotency key colliding with its persisted row. A full-suite run also showed the active worker can consume the fixed test message from the shared queue. The plan owns the integration test file and scopes changes to a unique per-invocation key and a dedicated temporary queue; it retains both same-key assertions and the SQS visibility/ack assertions. Coordinator review: accepted.
