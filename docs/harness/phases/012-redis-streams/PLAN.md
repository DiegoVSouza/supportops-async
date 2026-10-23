# PLAN — Redis Streams broker

allowed_write_paths: `supportops_async/queue/**`; `supportops_async/api/runtime.py`; `supportops_async/worker/**`; `pyproject.toml`; `uv.lock`; `tests/**`; `scripts/**`; `docs/harness/**`; `artifacts/packages/**`; `artifacts/evidence/phase-012-*`.

forbidden: remove SQS support, weaken crash/retry tests, change task API semantics, include secrets, publish a wheel, or change another project.

1. Add `RedisStreamBroker` to the existing broker contract with safe consumer-group creation, reclaim, visibility extension, ack, delayed retry and DLQ handling.
2. Configure P04 runtime from a Redis URL and queue prefix while preserving SNS event delivery and the SQS adapter.
3. Add contract and real Redis tests for duplicate delivery, visibility, retry limits, DLQ and recovery after a process restart.
4. Run P04 fast/full checks, build the versioned 0.1.4 wheel from the committed source, record provenance, and run an isolated consumer check.

LLM mode: fake. Stop if Redis cannot be run or recovery is not demonstrated.

Plan review: accepted; the product retains SQS compatibility while enabling a persistent self-hosted transport.
