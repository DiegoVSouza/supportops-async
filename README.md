# SupportOps Async Platform

An independently installable FastAPI and worker service for durable, asynchronous support workflows. The local demo uses a deterministic fake runner and makes no model or cloud calls.

## Architecture

```mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI
    participant P as PostgreSQL
    participant Q as SQS
    participant W as Worker
    participant S as SNS
    C->>A: POST /tasks + Idempotency-Key
    A->>P: Insert task, key, and task.created outbox row
    A->>Q: Publish task ID (at-least-once)
    A-->>C: 202 Accepted + task_id
    Q->>W: Deliver message (may repeat)
    W->>P: Claim with lease; read checkpoints/effect keys
    W->>P: Commit effect ledger and checkpoint atomically
    W->>P: Complete task and insert event outbox row
    W->>Q: Acknowledge message
    W->>S: Publish pending task.completed event
```

## Run the deterministic demonstration

```sh
uv sync --locked
uv run --locked python scripts/demo.py
```

The importable runtime package is pinned at version `0.1.0`. Build a local wheel without publishing it:

```sh
uv build --wheel --out-dir artifacts/packages
```

Run the abrupt process recovery case:

```sh
uv run --locked pytest -q --basetemp artifacts/evidence/.pytest-tmp tests/recovery/test_process_recovery.py
```

The test exits a child process after its effect and checkpoint commit, waits for the worker lease to expire, then starts another worker. It asserts the recorded effect is not run twice.

## Run PostgreSQL and LocalStack

```sh
docker compose -f docker-compose.async.yml config
docker compose -f docker-compose.async.yml up --build
```

Submit and retrieve a task:

```sh
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -H "Idempotency-Key: local-001" -d '{"payload":{"ticket_id":"T-100"},"steps":["triage","draft_reply"]}'
curl http://localhost:8000/tasks/<task_id>
```

To observe recovery during a long fake operation, submit `"step_delay_seconds":20` with two steps. After the first step finishes and the second starts, run `docker compose -f docker-compose.async.yml kill -s SIGKILL worker` and `docker compose -f docker-compose.async.yml up -d worker`. SQS visibility and the database lease delay redelivery until ownership expires; the next worker skips committed effects. Keep this local-only. Cancellation is observed between steps; an executing step is not forcibly interrupted.

## Task states

`queued → running → done | failed`; transient failures pass through `retrying`. Queued, retrying, and running tasks can be cancelled. Repeated `Idempotency-Key` values return the original task ID even if the payload differs; clients should reuse a key only for the same logical request.

## Delivery and failures

SQS is at-least-once. The idempotency key deduplicates submission, and each `(task_id, step)` effect key and checkpoint are committed together. This provides exactly-once behavior for the local fake effect ledger. A real external effect still needs its own idempotency key or shared transaction; this platform does not claim universal exactly-once delivery. Transient failures use bounded exponential visibility delay; permanent or exhausted failures go to the DLQ. SNS notifications use a transactional outbox, and unsent events remain pending for retry.

## Verification status

Unit and subprocess recovery tests use SQLite and an in-memory broker. They do not count as PostgreSQL/LocalStack integration or full-stack E2E. Those gates stay INCOMPLETE until run against local services. Terraform validation/plan and Docker image build also stay INCOMPLETE if their tools or daemon are unavailable. There are no live LLM metrics; `LLM_MODE=fake`, and model quality/cost metrics are PENDING.

## Infrastructure and authorization

Terraform templates declare local SQS, SNS, and a least-privilege worker policy with a LocalStack endpoint. The commands in `infra/terraform/README.md` are plan-only. Real AWS deployment, image push, or Terraform apply are outside the local demo and need separate authorization.
