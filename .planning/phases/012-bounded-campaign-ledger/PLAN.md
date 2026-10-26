# Plan — Bounded campaign ledger for P04

## Execution controls

- `llm_mode`: `fake`; no provider or service invocation in this phase.
- `allowed_write_paths`:
  - `.planning/phases/012-bounded-campaign-ledger/**`
  - `scripts/campaign_ledger.py`
  - `scripts/run_live_campaign.py`
  - `tests/test_campaign_ledger.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/decisions.md`
  - `docs/harness/failures.md`
  - `docs/harness/progress.md`
  - `docs/knowledge/live-campaign-ledger.md`
  - `artifacts/evidence/live-campaign-ledger/**`
- `forbidden_changes`: root `.env`, worker/API, provider planner, tool/effect/refund code, service configs/stacks, datasets/rubrics/approvals, historical acceptance evidence, other repositories, harness-kit, provider/network/Docker/build/service calls, budget increases, public deployment, external effects, and push.
- Budget: paid ceiling remains USD 0. Broad free-tier quota and cumulative call/token/cost/time limits remain `PENDING`; no existing single-workflow exception is reused.
- Validation: focused stdlib ledger tests, `-S` CLI help/dry-run/blocked generation, fast/full checks with Docker removed from subprocess `PATH` and `P04_SKIP_SERVICES=1`. Restore any check outputs that the existing full-gate script writes outside phase evidence.
- Stop condition: no campaign dispatcher, worker recovery, or provider call is implemented here. Missing any finite resource or review gate remains `INCOMPLETE`.

## Tasks

1. **Test durable call accounting and exclusivity** — immutable reservations/results, unknown usage, no trial rerun, cumulative cap race, process lease, and secret/content-free metadata.
2. **Implement P04-local ledger and resume inspection** — add append-only SQLite journal and OS lease; wire the broad campaign CLI with read-only resume while preserving its fail-closed generation path.
3. **Verify in offline mode and record honest limits** — run focused and full checks under service/Docker isolation, preserve historical artifacts/stacks, update project docs/knowledge, and review staged paths.

## Plan review

Reviewed against P04's service acceptance scope, Phase 011 caps, USD 0 profile, and portfolio live-readiness SPEC. The ledger records only campaign/case/trial and usage metadata; it does not accept task content or claim service readiness. Docker and service side effects are excluded from validation. Accepted for offline execution on 2026-10-26; clean-context review remains pending.
