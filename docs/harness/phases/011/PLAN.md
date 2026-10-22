# PLAN — Verify offline dependency recreation

allowed_write_paths: docs/harness/phases/011/**; docs/harness/progress.md; docs/harness/feature_list.json; artifacts/evidence/phase-011-**
forbidden_changes: product source; dependency lock; shared kit; sibling repositories; root roadmap; external deploy/publish/push/PR/merge; Terraform apply; live/paid LLM; modification or shutdown of pre-existing stacks.

llm_mode: fake

dependencies: committed `uv.lock`, installed uv CLI, local uv cache, Python 3.13. Docker services are not required for this dependency-only phase.

## Observable tasks
1. Review this plan and confirm the exact owned paths and isolated environment before execution.
2. Recreate all locked project and development dependencies in a fresh environment with uv offline mode; record exact command, exit code, and output.
3. Run the P04 fast gate from the recreated environment, record its result, then reconcile progress and portfolio matrix truthfully.

## Checks
`git diff --check`; `uv sync --offline --locked --all-groups` with `UV_PROJECT_ENVIRONMENT` set to a new temporary path; `uv run --offline --locked --no-sync python scripts/check_fast.py`; inspect evidence and staged diff for unrelated files or secrets.

## Stop condition
If Python 3.13 or cached distributions are unavailable, record the exact nonzero result as INCOMPLETE and stop this phase without network access or changing the lock. Do not run full service acceptance here.

## Plan review
Reviewed before execution: three observable tasks; dependency-only scope is isolated; no product source or lock change is expected; missing offline cache remains an honest INCOMPLETE result.
