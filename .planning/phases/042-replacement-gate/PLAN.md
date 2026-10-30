# Plan

1. Create a fresh isolated snapshot and Docker baseline with a unique owned namespace.
2. Run one full fake gate and clean only owned resources.
3. Preserve evidence and update the frozen-operation condition.

allowed_write_paths: `.planning/phases/042-replacement-gate/**`, `artifacts/evidence/reentrant-reviewed-operation-042/**`, `docs/harness/progress.md`.

forbidden_changes: source, frozen manifest, ledgers, provider/live invocation, credentials, policy, unowned Docker including `gossett_backend`, Terraform apply, fallback, capacity/reservation/counter changes, promotion claims. Stop on any pre-gate drift or uncertain result. Plan-check is implementer self-assessment.
