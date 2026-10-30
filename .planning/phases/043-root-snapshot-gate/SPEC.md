# Specification

Validate the offline corrections that no gate has exercised yet: `check_full.py` running `service_scenarios.py` through `uv run --locked` (`96b5b28`) and the container identity comparator (`82beb69`). Authority: root `AUTHORIZATION.md`, 2026-10-31, "one additional isolated full fake gate with corrected snapshot preparation".

The isolated snapshot must contain the enclosing lab root (`scripts/harness/`, `shared/policies/`, `.runtime/llm-live-readiness/`, and read-only copies of every project's live ledgers), which was the second cause of phase042's failure.

Done means: `check_full.py` exit 0, `provider_accessed: false` derived from unchanged ledger hashes and row counts, owned cleanup, and an empty global Docker identity diff.

Out of scope: any live dispatch. This gate does not authorize `local-reviewed-operation-040-v1`; the live operation is not the next action.
