# Failures

Record recurring builder or product failures here before fixing them.

## Implementation findings

- An initial unit run exposed an `UnboundLocalError` in outbox event creation caused by a function-local `uuid` import shadowing the module import. The local imports were removed and the full unit suite passes.
- pytest's default temporary directory could not be created reliably in the managed Windows environment. Checks now set `--basetemp artifacts/evidence/.pytest-tmp`; this directory is ignored.
- PostgreSQL, LocalStack, Docker daemon, and Terraform CLI are unavailable in this run. Their integration/build/plan gates remain INCOMPLETE rather than being represented by doubles.
- The prior standalone `uv pip install --offline` could not resolve `psycopg-binary==3.2.10` from cache. The project lock provides a reproducible path: `uv sync --locked --offline` now installs the complete 34-package environment successfully. Phase 005's new wheel smoke will use that lock-backed environment.

## 2026-10-26 — Live acceptance finding

The full Docker/PostgreSQL/SQS/Redis/Terraform gate passed. The first real workflow reached both provider steps but failed the reply output contract (488 input / 203 output tokens); its evidence is retained. The prompt now states explicit JSON key schemas. One corrective workflow passed with a real plan and two real worker calls (526 input / 195 output tokens), two persisted effects and no regeneration on duplicate delivery. Eight focused tests include rejection of missing, empty and non-object outputs. Failed attempt artifacts remain alongside the correction.

## 2026-10-26 — Phase 012 campaign ledger

- Unknown provider usage must retain the original pre-dispatch request/token/cost reservation. P04 tests this after both a crash-like reservation and an error completion.

## 2026-10-27 — Phase 017 isolated service invocation

- The initial isolated scenario invocation used guessed ports 16432/16566 although the checked-in Compose file binds 15432/14566. The command remained blocked on the unreachable endpoint and was interrupted before any application-level database or SQS request; phase-owned containers were then removed. The plan was corrected to the actual Compose bindings, availability rechecked, and the scenario completed successfully. Future isolated service plans must inspect Compose port mappings instead of assuming overrides.
- A direct pytest invocation without the repository root on `PYTHONPATH` failed collection for two `scripts.*` imports. Setting `PYTHONPATH=.` and running the configured `tests` path passed; this was an invocation issue, not a code/test failure.
- The full check can build the service image and run Terraform via Docker when the daemon is available. Validation set `DOCKER_HOST` to an unreachable loopback endpoint and omitted service variables; service/build gates are recorded as `INCOMPLETE`, and historical outputs were restored.

## 2026-10-27 — Phase 016 offline verification

- The managed Windows account cannot enumerate its default `pytest-of-dvsdi` temp directory (`PermissionError: WinError 5`). Phase 016 directs pytest `--basetemp` to its own ignored evidence subdirectory; focused tests then pass.
- `scripts/check_full.py` invokes Docker Compose configuration before checking daemon availability and does not catch a missing CLI executable. The full gate retained the installed CLI only for `docker compose ... config --quiet`, pointed daemon access at a nonexistent named pipe, and left Terraform unavailable. No build or service lifecycle command ran.
- The first isolated full-gate attempt also exposed that the child `pytest` entrypoint did not include the project root on `sys.path`; collection failed for two `scripts.*` imports. Re-running with `PYTHONPATH` set to the P04 root produced 67 passing tests and four expected service skips. The full gate reused `artifacts/evidence/.pytest-tmp`; its three pre-existing files were snapshotted and restored byte-for-byte.
