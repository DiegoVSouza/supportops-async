# Plan — Broker and worker

## allowed_write_paths
- `supportops_async/queue/**`, `supportops_async/worker/**`, `supportops_async/events/**`
- `tests/queue/**`, `tests/worker/**`, `tests/events/**`, `artifacts/**`, `docs/**`, `pyproject.toml`, `uv.lock`

## forbidden_changes
No relative sibling imports, real AWS calls, or changes to phase 001 public schemas without ADR.

## Tasks
1. Define broker message, handle, retry and DLQ contracts; implement in-memory test double.
2. Implement SQS/SNS adapter against LocalStack and contract tests.
3. Implement worker retry, ack/nack, visibility extension and deduplicated fake effects.

## Check and stop
Unit tests run with fake broker; integration only against local LocalStack. Stop on unavailable LocalStack and record INCOMPLETE rather than faking integration.
