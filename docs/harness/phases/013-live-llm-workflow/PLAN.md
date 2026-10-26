# P04 execution plan

## Task 1 — Test planner and workflow integration offline

Add tests for JSON parsing, allowlist/length validation, fail-closed mode, and a mocked plan passed to SQLiteTaskStore + InMemoryBroker + Worker. Assert durable completion and one effect per step.

## Task 2 — Implement optional Groq planner evaluation

Add pinned optional SDK dependency and a script to list models, request one structured plan from Groq, validate it, and run the existing local worker path. Persist sanitized artifact only; never persist user prompt or completion body.

## Task 3 — Verify and run one case

Run focused tests and the full offline P04 gate, then one preflight and one real plan request under free-tier limits. Analyze plan validity and task outcome; do not repeat a completed response.

## Ownership

`allowed_write_paths`: `docs/harness/phases/013-live-llm-workflow/**`, `scripts/run_live_groq_eval.py`, `tests/test_live_groq_eval.py`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/harness/decisions.md`, `docs/harness/progress.md`, `artifacts/evidence/phase-013-groq-*`.

`forbidden_changes`: `harness-kit/**`, `.env`, cloud config, database schemas, prior async behavior, other projects, and unrelated files.

## Runtime limits

- `LLM_MODE=live`; model `openai/gpt-oss-20b`; one ticket, one completion, <=128 output tokens, 20s timeout.
- Use only designated free-tier credentials, USD 0 configured paid budget, bounded retry/rotation for transient errors, no fallback. Report cost `PENDING` absent actual billing.
- Stop on quota, auth, invalid model/JSON/plan, or local workflow failure.

## Validation

Run P04's documented focused tests and full check. Save exact commands, exit codes, output and sanitized live result in phase-013 artifacts.
