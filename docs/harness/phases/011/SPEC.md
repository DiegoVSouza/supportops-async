# SPEC — Recreate locked dependencies without network access

Phase 010's incomplete service-gate run did not establish whether a clean dependency environment can be recreated offline. This phase answers that question using the committed `uv.lock`, the local uv cache, and an isolated disposable environment. It does not change product code or claim that arbitrary machines have the same cache.

Acceptance: `uv sync --offline --locked --all-groups` succeeds in a fresh environment; the project's fast gate succeeds from that environment; each command, exit code, and complete output is saved under `artifacts/evidence/`. If the local cache is insufficient, retain the failure as INCOMPLETE and do not fetch dependencies during the offline check.
