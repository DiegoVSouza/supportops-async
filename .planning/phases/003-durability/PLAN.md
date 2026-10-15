# Plan — Durability

## allowed_write_paths
- `supportops_async/store/**`, `supportops_async/worker/**`, `tests/recovery/**`, `artifacts/**`, `docs/**`

## forbidden_changes
No weakening idempotency assertions, no silent schema changes, no cloud deploy.

## Tasks
1. Specify checkpoint and idempotency key schema with migration.
2. Persist checkpoints around each simulated effect and enforce unique effect keys.
3. Kill/restart a local worker mid-task and verify resume without duplicate effects.

## Check and stop
Run unit crash simulation plus a subprocess-level integration recovery test; if DB/broker is absent, mark crash-recovery gate INCOMPLETE.
