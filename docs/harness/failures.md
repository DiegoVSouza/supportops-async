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

## 2026-10-27 — Phase 018 full-gate scratch safety

- `scripts/check_full.py` previously reused `artifacts/evidence/.pytest-tmp`; pytest clears its `--basetemp`, which contained three historical SQLite files. The gate now fails closed for existing/out-of-evidence temp paths and accepts a fresh phase-owned path. Guard refusal and before/after hashes are recorded in `artifacts/evidence/full-gate-018/`.
- The full gate's authorized image build replaced the existing P04-local `supportops-async:local-check` image tag. The pre-build inventory retained only short ID `d7ff4a414ee2`; the full digest was not captured. The new image is `sha256:5cc87bb6e992903af9b4a5dfa2c6e4a14a2d6d6a28f8a7fa37dfc34c8354e505`. Container/network/volume inventories were unchanged after phase cleanup. Record image-tag identities before future builds or use a unique tag if preserving an existing tag is required.
- The full check can build the service image and run Terraform via Docker when the daemon is available. Validation set `DOCKER_HOST` to an unreachable loopback endpoint and omitted service variables; service/build gates are recorded as `INCOMPLETE`, and historical outputs were restored.

## 2026-10-27 — Phase 016 offline verification

- The managed Windows account cannot enumerate its default `pytest-of-dvsdi` temp directory (`PermissionError: WinError 5`). Phase 016 directs pytest `--basetemp` to its own ignored evidence subdirectory; focused tests then pass.
- `scripts/check_full.py` invokes Docker Compose configuration before checking daemon availability and does not catch a missing CLI executable. The full gate retained the installed CLI only for `docker compose ... config --quiet`, pointed daemon access at a nonexistent named pipe, and left Terraform unavailable. No build or service lifecycle command ran.
- The first isolated full-gate attempt also exposed that the child `pytest` entrypoint did not include the project root on `sys.path`; collection failed for two `scripts.*` imports. Re-running with `PYTHONPATH` set to the P04 root produced 67 passing tests and four expected service skips. The full gate reused `artifacts/evidence/.pytest-tmp`; its three pre-existing files were snapshotted and restored byte-for-byte.

## 2026-10-27 — Phase 019 global TracerProvider collision

- Real API startup reported `Overriding of current TracerProvider is not allowed`; OTLP exporter setup created a provider that could not become global. The task still completed and Jaeger received the worker span only; API span was absent. Preserve task `ac52c679-8226-4658-9eca-6739e4caf906`, trace `4bf92f3577b34da6a3ce929d0e0e4736`, and the one failed synthetic probe. No semantic replay is allowed.
- Offline/fast checks cannot expose the provider collision. Correct the setup by inspecting/adopting an existing SDK provider or locating who sets it before app lifespan, then test idempotence and service/resource attribution in a new phase before another service probe.

## 2026-10-27 — Phase 020 probe verifier failure and reconciliation

- The one-shot service task completed, but its first verifier raised `TypeError` while hashing Jaeger tag dictionaries. The task and trace are preserved; the task was not replayed. A GET-only query of that same trace passed the API+worker correlation, service identity, scalar bounded attribute, allowlist, and UUID-free checks. A subsequent GET after intentional stack teardown failed with connection refused and made no submission.
- Phase 019's global-provider collision is fixed in candidate `beff749202805b138d820daaddb80a4468afc7c9`: existing SDK providers are adopted only when `service.name` matches; global state is not replaced. The full local gate and exact Docker inventory reconciliation passed. Keep phase-019 failure evidence immutable.
