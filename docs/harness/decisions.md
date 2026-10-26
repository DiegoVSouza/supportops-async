# Intake decisions — P04 Async AI Platform

- Product: independently installable FastAPI service and worker package for durable asynchronous tasks, idempotency, retries, and event delivery.
- Measurable success: API contract tests prove idempotency/status/cancel; worker tests prove duplicate delivery causes one simulated effect, crash resumes checkpoints, and permanent failures reach DLQ after the configured retry count.
- Profile: `workflow-automation`; this is an API-backed durable workflow with no product LLM runtime. `LLM_MODE=fake` only for a worker demonstration.
- Runtime: Python 3.13; local Postgres + LocalStack SQS/SNS; no cloud credentials required. Kafka is excluded unless a separate ADR justifies it.
- Risk: side effects are simulated locally and idempotent. No real refunds, deployment, or external service calls in checks. No sensitive data or multi-tenant behavior in this project.
- Dependencies: P00/P01 are optional adapters behind local protocols during parallel development. No sibling-source imports. P05 may install a versioned package only after approval and artifact hash recording.
- Budget: no paid LLM spend; phase 013 uses only the explicitly permitted Groq free-plan allowance for one plan. The production worker remains provider-agnostic.
- Public contracts: `Broker`, `TaskStore`, task status model, and HTTP routes follow the original P04 brief; changes require ADR and versioned consumer updates.
- Phase 013 decision (2026-10-26): evaluate an opt-in Groq-generated allowlisted task plan using only SQLite and in-memory broker/worker contracts. The production worker stays provider-agnostic; no cloud services or paid LLM calls are enabled. Fake remains the default.

## 2026-10-26 — Live Docker acceptance

Use opt-in Groq live mode with numbered credentials and authenticated model preflight. Preserve deterministic fake defaults and fail closed on provider/contract failures. Only local synthetic acceptance and the designated free allowance are authorized; billed cost remains PENDING. Evidence: artifacts/evidence/live-docker/.
