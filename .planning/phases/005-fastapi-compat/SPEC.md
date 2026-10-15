# SPEC — FastAPI consumer compatibility

## Goal

Publish a compatible patch of `supportops-async` for consumers that pin FastAPI 0.142.4, without changing the P04 HTTP contract.

## Acceptance criteria

- The existing API contract tests and local unit/recovery suite pass under FastAPI 0.142.4.
- The P04 runtime declares a tested FastAPI compatibility interval beginning at 0.142.4 and ending before 0.143.0; the dependency lock resolves the exact tested version.
- The compatibility decision records the FastAPI 0.142.0/0.142.4 release notes, the OpenTelemetry dependency change, and why the P04 app remains compatible.
- The package version increases by one patch version and its built wheel metadata includes the compatible FastAPI requirement.
- A local wheel install and smoke test verify imports from the installed wheel, its HTTP route, and its durable task behavior.
- No P05 files, public P04 routes/statuses, external publication, or cloud services are changed.

## Out of scope

PostgreSQL/LocalStack integration, container build, Terraform, and live model evaluation remain governed by their existing gates.
