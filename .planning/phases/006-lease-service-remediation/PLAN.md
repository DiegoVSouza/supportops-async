# Plan — Phase 006: Lease and service-backed durability remediation

```yaml
project: p04
requirement_ids: [P04-006-001, P04-006-002, P04-006-003, P04-006-004]
allowed_write_paths:
  - .planning/phases/006-lease-service-remediation/**
  - supportops_async/worker/**
  - supportops_async/store/**
  - tests/**
  - scripts/**
  - docker-compose.async.yml
  - Dockerfile
  - infra/**
  - .github/workflows/**
  - docs/**
  - artifacts/evidence/**
  - docs/harness/feature_list.json
  - docs/harness/progress.md
  - README.md
  - README.pt-BR.md
forbidden_changes:
  - shared/**
  - harness.yaml
  - .harness/**
  - public task/API contract changes without ADR, version update, and consumer update
  - weakened tests or claims of universal exactly-once delivery
  - cloud deploy, Terraform apply, image push, package publication, Git push, PR, or merge
dependencies:
  - Existing P04 local fake/SQLite recovery test environment
  - PostgreSQL and LocalStack endpoint/credentials for service integration; if absent, record INCOMPLETE
  - Docker daemon for Compose/image validation; Terraform CLI for validate/plan; if absent, record INCOMPLETE
llm_mode: fake
checks:
  - Unit/contract and local subprocess recovery: `uv run pytest -q`
  - Service integration: `uv run pytest -q -m service` (use repository's configured service marker/command; save output)
  - Compose validation/runtime: `docker compose -f docker-compose.async.yml config` and service smoke when daemon exists
  - Image: `docker build -f Dockerfile -t supportops-async:local .`
  - IaC: `terraform -chdir=infra validate` and non-applying `terraform -chdir=infra plan`
  - Full required gate: repository full-check command; preserve nonzero status for unavailable mandatory gates
evidence_directory: artifacts/evidence/
stop_condition: Stop service-dependent execution when required services/CLIs are unavailable, save the exact command, exit code, and output as INCOMPLETE, and do not mark the full required gate PASS. Stop before any external publication/deployment or public contract change lacking an approved ADR/version plan.
```

## Context needed
Read this phase SPEC/VERIFY, `docs/harness/decisions.md`, `docs/harness/progress.md`, `docs/harness/feature_list.json`, the existing worker/store contracts and migrations, prior recovery/infrastructure phase evidence, and the original P04 brief. Do not rely on sibling source trees.

## Tasks
1. **Keep leases alive during long steps.** Implement database lease renewal and broker visibility extension through the duration of a running step. Add a deterministic test whose step exceeds both configured intervals and checks competing-worker behavior.
2. **Prove service-backed durability.** Add/run PostgreSQL plus LocalStack cases for crash recovery, duplicate delivery/effect idempotency, bounded retries, and DLQ. Preserve separate labels for unit, local subprocess, and service integration; never weaken existing assertions.
3. **Complete operational gates and state.** Run Compose, image, and Terraform checks where available; ensure mandatory missing gates make the full gate return nonzero/INCOMPLETE. Update delivery-guarantee docs, feature statuses, and progress from saved evidence.

## Plan review
Coordinator review before execution: accepted for scope and ownership. The three tasks are observable and cover the four requirements; product paths are confined to P04; service/tool absence has an explicit INCOMPLETE branch; checks do not apply Terraform or publish artifacts. Record actual command outputs under `artifacts/evidence/` during execution.

## Stop condition
Stop only after the three tasks have evidence-backed PASS/INCOMPLETE/PENDING results and state/docs match that evidence. Missing dependencies must remain INCOMPLETE; model metrics remain PENDING. No external action is in scope.
