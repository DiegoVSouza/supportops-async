# Phase 001 — API and task store

## Goal and acceptance
Expose the versioned task HTTP contract and persistent idempotent task creation/status/cancellation. Repeated `Idempotency-Key` returns the original task ID; other callers cannot mutate an already claimed task through a duplicate create. Status transitions are validated and progress/results serialize deterministically.

## Scope
`supportops_async.api` and `supportops_async.store`; local SQLite may support unit tests while Postgres integration is tested separately. No sibling imports.
