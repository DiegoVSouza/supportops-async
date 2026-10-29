# Plan

1. Refuse both legacy entry points and test they cannot read credentials, call providers or start services.
2. Run locked fake tests and fast validation; record sanitized command, cwd, exit and output.

allowed_write_paths: `.planning/phases/028-disable-unaccounted-live/**`, `scripts/run_live_groq_eval.py`, `scripts/run_live_service_eval.py`, `supportops_async/live_groq.py`, `tests/test_legacy_live_guard.py`, `artifacts/evidence/disable-unaccounted-live-028/**`.

forbidden_changes: historical artifacts, other projects, budgets, credentials, live calls, existing assertions, Docker lifecycle, Terraform apply, paid use and external effects. Budget zero calls and USD 0. max_tries: 3 per failure; no completion replay. Plan-check is implementer self-assessment. Stop on unexpected external access.
