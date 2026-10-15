# Phase 006 — Lease and service-backed durability remediation

## Objective
Close the evidenced P04 durability gaps by keeping database leases and broker visibility alive during long steps, then verify retry, recovery, idempotency, and DLQ semantics against PostgreSQL and LocalStack when those services are available.

## Requirements
- [ ] P04-006-001: A step that exceeds the configured lease and visibility intervals retains ownership through renewal; competing workers cannot concurrently claim the same active task.
- [ ] P04-006-002: PostgreSQL and LocalStack tests exercise crash recovery, bounded retries, DLQ delivery, duplicate delivery, and effect-ledger idempotency. SQLite/fake results remain separately labeled.
- [ ] P04-006-003: Compose runtime, non-root image build, and Terraform validate/plan are executed when Docker and Terraform are available; unavailable dependencies produce INCOMPLETE evidence and a nonzero required full-gate result.
- [ ] P04-006-004: Delivery guarantees and all feature/progress states accurately distinguish PASS, INCOMPLETE, and PENDING; the effect ledger is not described as universal exactly-once delivery.

## Out of scope
Cloud deployment, Terraform apply, image publication, Git push, public contract changes without an ADR and versioned consumer update, and changes to shared harness/kit or sibling projects.

## Acceptance criteria
- Given a worker step longer than the lease/visibility interval, when another worker polls, then the original worker retains its lease or safely yields ownership without duplicate effects.
- Given a PostgreSQL/LocalStack service environment, when the recovery suite runs, then crash recovery, bounded retry, DLQ, and duplicate-effect cases pass with saved service-integration evidence.
- Given a missing Docker daemon, Terraform CLI, or service endpoint, when the full gate runs, then that gate exits nonzero and records INCOMPLETE with command, exit code, and output.
- Given the local effect ledger deduplicates an effect key, when documentation is reviewed, then delivery semantics still state at-least-once delivery and scope idempotency to tracked effects.
