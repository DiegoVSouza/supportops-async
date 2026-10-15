# Intake decisions — P04 Async AI Platform

- Product: independently installable FastAPI service and worker package for durable asynchronous tasks, idempotency, retries, and event delivery.
- Measurable success: API contract tests prove idempotency/status/cancel; worker tests prove duplicate delivery causes one simulated effect, crash resumes checkpoints, and permanent failures reach DLQ after the configured retry count.
- Profile: `workflow-automation`; this is an API-backed durable workflow with no product LLM runtime. `LLM_MODE=fake` only for a worker demonstration.
- Runtime: Python 3.13; local Postgres + LocalStack SQS/SNS; no cloud credentials required. Kafka is excluded unless a separate ADR justifies it.
- Risk: side effects are simulated locally and idempotent. No real refunds, deployment, or external service calls in checks. No sensitive data or multi-tenant behavior in this project.
- Dependencies: P00/P01 are optional adapters behind local protocols during parallel development. No sibling-source imports. P05 may install a versioned package only after approval and artifact hash recording.
- Budget: no LLM spend; external provider calls disabled.
- Public contracts: `Broker`, `TaskStore`, task status model, and HTTP routes follow the original P04 brief; changes require ADR and versioned consumer updates.
