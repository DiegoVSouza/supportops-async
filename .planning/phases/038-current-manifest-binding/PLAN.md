# Plan

1. Confirm P04 and root source provenance, exact applied migration audit, existing operation history and manifest absence without reading credentials.
2. Freeze one current manifest through the existing create-only helper, then validate its candidate/fingerprint/policy binding offline.
3. Record sanitized command evidence and stop. A new full gate authorization and current service validation remain required before any reservation or live dispatch.

allowed_write_paths: `.planning/phases/038-current-manifest-binding/**`, `artifacts/evals/live/local-revalidation-v1/manifest.json`, `artifacts/evidence/current-manifest-binding-038/**`, `docs/harness/progress.md`.

forbidden_changes: source code, policy, ledgers, reservations, invocation/live-result markers, historical reports, credentials, provider/live calls, Docker/services, Terraform apply, paid usage, fallback, holdout or human-review claims. Fake/offline only; provider calls0, paidUSD0. Stop on stale root audit, uncommitted source, existing manifest, consumed operation marker, or authority/history mismatch.
