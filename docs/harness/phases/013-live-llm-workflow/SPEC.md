# P04 live LLM workflow-plan evaluation

## Status

Implemented and verified with one real plan passed through the SQLite store, memory broker, and worker. External service, Docker, and Terraform gates remain unavailable in this environment.

## Goal and selection

Add a bounded optional Groq planner that converts one synthetic support request into an allowlisted P04 task-step plan, then pass that plan through the existing in-memory durable task store, broker, and worker. P04's product is asynchronous workflow delivery; it currently uses only a fake step runner.

## Requirements

- Use official Groq SDK and `openai/gpt-oss-20b` after authenticated model preflight; explicit live mode only.
- Ask for structured JSON containing only the allowlisted steps `triage` and `draft_reply`; reject other names, empty plans, or more than two steps.
- Feed the validated plan into the existing SQLite store + in-memory broker worker and assert one task completes with idempotent effects recorded. Do not connect Postgres, Redis, SQS, or cloud services for this small evaluation.
- Load root `.env` silently; support bounded key rotation only for retryable throttling/transient errors; no fallback provider.
- One model completion, max 128 output tokens, timeout 20s, configured task budget USD 0; use only the user-designated Groq free allowance. Keep offline fake runner unchanged.
- Record model, planned steps, task outcome, usage, retries, cost as `PENDING` unless billing confirms, command/exit, and sanitized failure class. Do not store ticket prompt or raw answer.

## Acceptance

1. Offline tests validate strict plan parsing/allowlisting, no provider call in fake mode, and worker completion/idempotency.
2. Full offline P04 validation remains green.
3. One live-generated plan is validated then processed by the real local durable workflow contracts, or a sanitized failure is recorded.
4. No cloud services, credentials, prompt, or raw provider body appear in artifacts.

## Scope

P04-local script, tests, optional SDK extra, docs and evidence only. No worker state machine changes, schema migrations, kit changes, or sibling edits.

## Verified references

- Model JSON/tool output support: [Groq GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b).
- Free-plan limits and `Retry-After`: [Groq rate limits](https://console.groq.com/docs/rate-limits).
- Official Python SDK pin: [groq-python 1.7.0](https://github.com/groq/groq-python/releases/tag/v1.7.0).
