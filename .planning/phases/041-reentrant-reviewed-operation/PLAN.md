# Plan

1. Retarget the controller, owner allocation, manifest and isolated evidence paths to the root-authorized `-040-` identity; preserve the stopped `-038-` paths.
2. Add/adjust offline tests for fresh identity, authority, held-lease migration verification, duplicate/reservation/crash no-replay behavior; run locked focused controls.
3. Commit a frozen candidate and prepare one isolated fake gate with explicit Docker baseline/namespace. Dispatch remains conditional on a PASS gate and frozen manifest.

allowed_write_paths: `scripts/revalidation_operation.py`, `evals/live-execution.json`, `tests/test_revalidation_operation.py`, `.planning/phases/041-reentrant-reviewed-operation/**`, `docs/harness/{progress.md,feature_list.json}`, `artifacts/evidence/reentrant-reviewed-operation-041/**`, `artifacts/evals/live/local-reviewed-operation-040-v1/manifest.json`.

forbidden_changes: root policy/migration/guard, existing ledger/provider receipts, predecessor manifests/evidence, credentials, fallback, capacity expansion, reservation release, counter reset, holdout/confirmation, `gossett_backend`, Terraform apply, deployment/push/PR, and human-review/promotion claims.

Fake is default. Gate budget is one separately authorized fake validation; live operation is at most once only after PASS controls. Stop on stale source, failed gate, uncertain invocation, history mismatch, or service ownership ambiguity. Plan-check is implementer self-assessment.
