# Failures

Record recurring builder or product failures here before fixing them.

## Implementation findings

- An initial unit run exposed an `UnboundLocalError` in outbox event creation caused by a function-local `uuid` import shadowing the module import. The local imports were removed and the full unit suite passes.
- pytest's default temporary directory could not be created reliably in the managed Windows environment. Checks now set `--basetemp artifacts/evidence/.pytest-tmp`; this directory is ignored.
- PostgreSQL, LocalStack, Docker daemon, and Terraform CLI are unavailable in this run. Their integration/build/plan gates remain INCOMPLETE rather than being represented by doubles.
- The prior standalone `uv pip install --offline` could not resolve `psycopg-binary==3.2.10` from cache. The project lock provides a reproducible path: `uv sync --locked --offline` now installs the complete 34-package environment successfully. Phase 005's new wheel smoke will use that lock-backed environment.

## 2026-10-26 — Live acceptance finding

The full Docker/PostgreSQL/SQS/Redis/Terraform gate passed. The first real workflow reached both provider steps but failed the reply output contract (488 input / 203 output tokens); its evidence is retained. The prompt now states explicit JSON key schemas. One corrective workflow passed with a real plan and two real worker calls (526 input / 195 output tokens), two persisted effects and no regeneration on duplicate delivery. Eight focused tests include rejection of missing, empty and non-object outputs. Failed attempt artifacts remain alongside the correction.
