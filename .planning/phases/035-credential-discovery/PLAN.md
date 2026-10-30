# Plan

1. Inspect the existing P04 wrapper, shared provider key selection and process environment semantics; define a finite new wrapper that uses either root `.env` or process values without weakening the single-use guard.
2. Implement deterministic safe discovery and fake contract tests for missing, process-only, root-only, precedence and sanitized output. Keep actual provider access and service startup disabled in tests.
3. Record offline evidence and the remaining full-gate/current-binding prerequisites. Do not run a focused service gate or dispatch operation032.

allowed_write_paths: `.planning/phases/035-credential-discovery/**`, `scripts/credential_presence.py`, `tests/test_credential_presence.py`, `artifacts/evidence/credential-discovery-035/**`.

forbidden_changes: historical phase032 wrapper/evidence, policy, ledgers, reservations, user outputs, Docker resources, model/provider calls, fallback, paid usage, Terraform apply, human/holdout/promotion. Fake only; paidUSD0, provider calls0. Preserve P04 historical gate3/3 plus exception1/1 consumed. Stop on ambiguous key source or unsafe credential handling. Plan-check is implementer self-assessment.
