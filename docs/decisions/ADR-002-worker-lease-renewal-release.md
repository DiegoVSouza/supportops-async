# ADR-002: Release active-step lease renewal

- Status: Accepted
- Date: 2026-10-15

## Context

Version 0.1.1 renews task leases and SQS visibility only between worker steps. A long-running step can outlive both intervals, allowing another worker to claim the same task while the first runner is still executing. The 0.1.2 change renews both while each step runs and validates the behavior with a local long-step test. This is a runtime behavior fix; the public API and package contracts remain unchanged.

## Decision

Release the fix as the next patch version, `supportops-async` 0.1.2. Build and retain the wheel locally with source commit, dependency lock hash, and wheel SHA-256. Consumers must install the versioned wheel and pass a consumer smoke before treating the updated runtime as integrated. Do not publish the wheel externally as part of this phase.

## Evidence

- `artifacts/evidence/phase-006-unit-suite.txt`: local suite passes with long-step lease and visibility renewal covered; PostgreSQL and LocalStack tests are skipped when endpoints are not configured.
- `artifacts/evidence/phase-006-full-gate.txt`: required full gate is INCOMPLETE because PostgreSQL, LocalStack, Docker daemon, and Terraform CLI are unavailable.
- Build, artifact hash, and installed-wheel consumer smoke are recorded in the 0.1.2 package provenance after the source commit.

## Consequences

- The behavior fix is consumable through an immutable local wheel with verifiable provenance.
- Existing 0.1.1 artifacts remain retained as historical versions.
- Service-backed guarantees remain unproven until PostgreSQL and LocalStack runs succeed; no universal exactly-once claim is implied.
