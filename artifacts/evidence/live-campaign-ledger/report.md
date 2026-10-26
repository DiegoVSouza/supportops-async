# Phase 012 — P04 bounded campaign ledger

Status: `INCOMPLETE`. Offline ledger functionality passes; the full service gate remains incomplete and the campaign is blocked.

## Evidence

| Command | Exit | Result |
|---|---:|---|
| `uv run --locked pytest tests/test_campaign_ledger.py -q` | 0 | 6 ledger tests passed. |
| `uv run --locked pytest tests/test_live_campaign_preparation.py -q` | 0 | 11 campaign/grader tests passed. |
| `uv run --locked python scripts/check_fast.py` | 0 | Fast project check passed. |
| `uv run --locked python scripts/check_full.py` with `PYTHONPATH=.` and `DOCKER_HOST=tcp://127.0.0.1:1` | 2 | 60 tests passed, 4 service tests skipped; Compose config passed. Full result is `INCOMPLETE` because PostgreSQL/LocalStack/Redis are not configured and Docker image/Terraform validation was intentionally isolated. |
| `uv run --locked python -S scripts/run_live_campaign.py --help` | 0 | Stage and read-only resume options available. |
| `uv run --locked python -S scripts/run_live_campaign.py --stage pilot --dry-run` | 0 | Reports 18-call maximum pilot and pending caps without provider or Docker mutation. |
| `uv run --locked python -S scripts/run_live_campaign.py --stage pilot` | 2 | Broad generation blocked by pending approvals, quota, and cumulative ceilings. |

Historical live evidence, service outputs, and runtime stacks were preserved. The Docker daemon was not used to build or run containers in this phase.

## Remaining gates

- Actual API/worker service with PostgreSQL, LocalStack SQS, and Redis, plus crash-boundary behavior and lease integration.
- Groq catalog preflight/dispatch, independent dataset/rubric review, finite free quota and cumulative limits, confirmation funding, pacing/time ceilings.
- Service canary, rollback, clean-context review. No provider call or workflow effect was performed in this phase.
