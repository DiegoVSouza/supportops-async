# Failures

Record recurring builder or product failures here before fixing them.

## Implementation findings

- An initial unit run exposed an `UnboundLocalError` in outbox event creation caused by a function-local `uuid` import shadowing the module import. The local imports were removed and the full unit suite passes.
- pytest's default temporary directory could not be created reliably in the managed Windows environment. Checks now set `--basetemp artifacts/evidence/.pytest-tmp`; this directory is ignored.
- PostgreSQL, LocalStack, Docker daemon, and Terraform CLI are unavailable in this run. Their integration/build/plan gates remain INCOMPLETE rather than being represented by doubles.
- The prior standalone `uv pip install --offline` could not resolve `psycopg-binary==3.2.10` from cache. The project lock provides a reproducible path: `uv sync --locked --offline` now installs the complete 34-package environment successfully. Phase 005's new wheel smoke will use that lock-backed environment.
