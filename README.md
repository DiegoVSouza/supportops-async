# SupportOps Async Platform

An independently installable FastAPI and worker service for durable, asynchronous support workflows. The local demo uses a deterministic fake runner and makes no model or cloud calls.

## Problem

Support work can continue after an HTTP response and a broker may deliver the same message more than once. The service needs durable task state, explicit retry behavior, and a record of completed effects.

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

## Quickstart

```sh
uv sync --locked
uv run --locked python scripts/demo.py
```

The importable runtime package is pinned at version `0.1.3`. Build a local wheel without publishing it:

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

When the default host ports are already occupied, use the committed verification override; it binds PostgreSQL to 15432, LocalStack to 14566, and the API to 18000 without changing ports used by other stacks:

```sh
docker compose -p p04-remediation -f docker-compose.async.yml -f docker-compose.remediation.yml up -d --build
```

Submit and retrieve a task:

```sh
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -H "Idempotency-Key: local-001" -d '{"payload":{"ticket_id":"T-100"},"steps":["triage","draft_reply"]}'
curl http://localhost:8000/tasks/<task_id>
```

To observe recovery during a long fake operation, submit `"step_delay_seconds":20` with two steps. After the first step finishes and the second starts, run `docker compose -f docker-compose.async.yml kill -s SIGKILL worker` and `docker compose -f docker-compose.async.yml up -d worker`. SQS visibility and the database lease delay redelivery until ownership expires; the next worker skips committed effects. Keep this local-only. Cancellation is observed between steps; an executing step is not forcibly interrupted.

## How it works

`queued → running → done | failed`; transient failures pass through `retrying`. Queued, retrying, and running tasks can be cancelled. Repeated `Idempotency-Key` values return the original task ID even if the payload differs; clients should reuse a key only for the same logical request.

## Delivery and failures

SQS is at-least-once. The idempotency key deduplicates submission, and each `(task_id, step)` effect key and checkpoint are committed together. This provides exactly-once behavior for the local fake effect ledger. A real external effect still needs its own idempotency key or shared transaction; this platform does not claim universal exactly-once delivery. Transient failures use bounded exponential visibility delay; permanent or exhausted failures go to the DLQ. SNS notifications use a transactional outbox, and unsent events remain pending for retry.

## Results

The deterministic unit and recovery layer runs with SQLite and in-memory adapters. The full local gate passed with 31 tests, PostgreSQL, LocalStack, long-lease, duplicate-delivery, retry/DLQ, image-build, and Terraform `init`, `validate`, and LocalStack-only `plan` scenarios. The worker crash recovery path after an effect commit also passed. No Terraform apply or live LLM calls were run; model quality and cost metrics remain PENDING. Evidence is in `artifacts/evidence/comment-cleanup-services.txt`.

## Design decisions

Terraform templates declare local SQS, SNS, and a least-privilege worker policy with a LocalStack endpoint. The commands in `infra/terraform/README.md` are plan-only. Real AWS deployment, image push, or Terraform apply are outside the local demo and need separate authorization.

## Testing

Phase 010 closes the early-redelivery data-loss case in version 0.1.3. If a broker message arrives before the PostgreSQL lease expires, the worker defers it instead of acknowledging it; retry caps count actual store claims. A real subprocess was killed after committing an effect, a message was redelivered before lease expiry and deferred, and recovery after lease expiry skipped the recorded effect and completed the remaining work. The PostgreSQL/LocalStack full gate also passed long-step heartbeat, duplicate delivery, retry exhaustion/DLQ, image build, and Terraform init/validate/plan (no apply). See `artifacts/evidence/phase-010-full-gate.txt` and `phase-010-early-redelivery-green.txt`. Local ledger idempotency does not guarantee exactly-once arbitrary external effects.

## Limitations

The ledger protects the simulated local effect. A real external system still needs its own idempotency boundary or shared transaction. `LLM_MODE=fake` is the only model mode used here.
