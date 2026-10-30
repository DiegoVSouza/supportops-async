# Plan

1. Retain the external migration check before acquiring the campaign lease; inside that lease, verify the applied audit, policy and ledger prefixes under the account lease without reacquiring the campaign lease.
2. Add fake tests for lock ordering, missing/applied audit, changed prefixes and no provider dispatch; run targeted offline tests and check_fast.
3. Record evidence and preserve the consumed operation and stale manifest; do not run a full gate or provider call.

allowed_write_paths: `.planning/phases/040-reentrant-migration-check/**`, `scripts/revalidation_operation.py`, `tests/test_revalidation_operation.py`, `artifacts/evidence/reentrant-migration-check-040/**`, `docs/harness/progress.md`.

forbidden_changes: policy, migration audit, ledgers, reservations, historical manifests/results, Docker, credentials, provider/live calls, paid use, fallback, holdout or human review. Fake/offline only. Stop on invalid audit, pending migration or unverifiable ledger history. Plan-check is implementer self-assessment.
