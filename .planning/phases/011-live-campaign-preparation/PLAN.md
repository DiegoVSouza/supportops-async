# Plan — Live campaign preparation

## Execution controls

- `llm_mode`: `fake`; preparation and dry-run are offline.
- `allowed_write_paths`:
  - `.planning/phases/011-live-campaign-preparation/**`
  - `evals/datasets/live-v1/**`
  - `evals/rubrics/live-v1/**`
  - `evals/live-campaign.json`
  - `scripts/run_live_campaign.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/decisions.md`
  - `artifacts/evidence/live-campaign-preparation/**`
- `forbidden_changes`: API/worker/runtime and prompts, database/broker adapters, Docker/Terraform configuration, other repositories, harness-kit, root `.env`, secrets, historical evidence, provider calls, Docker mutation, cloud deployment, real refunds/effects, or paid spend.
- Budget source: P04 profile and decisions authorize no paid LLM spend. Existing one-plan free-tier exception does not authorize a 60-case campaign, three trials, confirmation set or extra calls. All expanded capacity and spend reservations are `PENDING`; numbered credentials are not separate quotas.
- Planned load to display, not authorization: pilot 6 development cases × 1 trial × at most 3 calls = 18 calls; full 60 × 3 × 3 = 540 calls before confirmation. Unknown provider capacity or cost blocks generation.
- Validation: P04 safe fast/fake checks, dataset/split/rubric contracts, deliberate invalid plan/effect outcomes, dry-run isolation and blocked-generation tests. Save command, exit code and sanitized output under the evidence path. Full checks with Docker/Terraform are deferred until their side effects and stack ownership are reviewed.
- Stop condition: no campaign generation until budget/quota, model preflight, reviewer capacity, local dependency ownership/ports, timeout targets, and case/rubric review are approved and evidenced. Preserve incomplete service prerequisites as `INCOMPLETE`.

## Tasks

1. **Freeze the API/worker scenarios and rubrics** — inspect the actual HTTP and worker contracts, crash/recovery tests, and task policies. Author 60 unique synthetic cases in the fixed 18/42 split and 36/24 language balance; require real service applicability, not demo-only success.
2. **Build the preparation dry-run and reservation config** — validate the stage/config contract and display cases, trials, 18/540 call ceilings, approval gaps and confirmation reserve without SDK construction, credentials, network or Docker. Block generation while campaign ceilings are pending.
3. **Prove grader and preparation safety** — reject invalid step order/plans, duplicate committed effects, unauthorized effects after cancellation/auth expiry, and misclassified provider-response/effect-commit crashes. Run safe fake checks, save evidence, and review the staged diff.

## Plan review

Coordinator review completed against P04's provider-agnostic production worker decision, existing service/crash contracts, and portfolio requirements. The 18/42 split, 36/24 language allocation, three-call cap, and 18/540 pilot/full ceilings are consistent. The path boundary excludes runtime and infrastructure changes until a later reviewed phase. Accepted for preparation execution on 2026-10-26. A clean-context verifier is still required for finished phase gates.
