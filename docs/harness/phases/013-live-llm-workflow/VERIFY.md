# P04 verification

- Review plan ownership: P04-local only; no cloud, migration, or kit changes.
- Run new planner/parser integration tests and full P04 offline gate with live mode unset. Save command, exit code, and output.
- Query authenticated Groq models, confirm `openai/gpt-oss-20b`, then make at most one completion with 128 output tokens.
- Verify the returned step plan is allowlisted, P04 local worker completes it, and idempotency ledger contains one effect per step.
- Save sanitized result, actual model/usage, retries, status, command and exit code; leave cost `PENDING` unless billing confirms.
- Inspect staged diff for credentials and commit locally without pushing.

## Recorded result — 2026-10-26

- Focused parser tests passed (7). Full check: 35 passed, 4 skipped; local worker/store checks passed. Overall `INCOMPLETE` only for unavailable PostgreSQL, LocalStack, Docker and Terraform prerequisites.
- Live command: `LLM_MODE=live uv run --extra live --group dev python scripts/run_live_groq_eval.py`; exit 0. Four-key model preflight passed; 1 completion generated a two-step allowlisted plan; SQLite task completed and one effect per step was recorded. Usage: 120 input / 25 output tokens. Cost remains `PENDING`.
- No cloud service or external action was used. Fake runner is unchanged.
