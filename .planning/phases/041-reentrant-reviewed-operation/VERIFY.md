# Verification

Focused PASS: `uv run --locked python -m pytest -q tests/test_revalidation_operation.py` exited 0 (13 passed), then `uv run --locked python scripts/check_fast.py` exited 0.

Full gate INCOMPLETE and consumed: isolated preparation and Compose startup passed, but the execution host interrupted after the durable consumption marker and before `check_full.py` produced a result. The owned namespace was removed with `docker compose ... down --volumes --remove-orphans`; no provider or live operation was invoked. The gate cannot be replayed, so the bounded live replacement operation remains blocked.
