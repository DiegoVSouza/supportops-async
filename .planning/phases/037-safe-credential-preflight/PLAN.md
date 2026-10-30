# Plan

1. Define the wrapper preflight contract from the existing safe credential-presence helper, including root-only, process-only, combined and absent slots without values.
2. Integrate that preflight before service startup, marker creation or provider imports, and add offline tests that prove all stop/allow shapes and preserve no-dispatch behavior.
3. Run fake/locked targeted validation, record sanitized evidence and retain the stale-manifest/full-gate/live-operation stop conditions.

allowed_write_paths: `.planning/phases/037-safe-credential-preflight/**`, `scripts/credential_presence.py`, `scripts/revalidation_operation.py`, `tests/test_credential_presence.py`, `tests/test_revalidation_operation.py`, `artifacts/evidence/safe-credential-preflight-037/**`, `docs/harness/progress.md`.

forbidden_changes: policy, ledgers, reservations, invocation markers, manifest, historical reports, `gossett_backend`, Docker resources, customer data, provider/live calls, fallback, paid usage, Terraform apply, holdout or human-review claims. Fake/offline tests only; provider calls0, paidUSD0. Stop before dispatch on any ambiguity or existing invocation. This phase does not consume or replace a full gate.
