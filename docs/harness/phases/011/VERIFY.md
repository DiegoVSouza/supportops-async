# VERIFY — Offline dependency recreation

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Locked dependencies in fresh temporary environment, offline | `uv sync --offline --locked --all-groups --python 3.13` with `UV_PROJECT_ENVIRONMENT` set to a new temp path | 0 | `artifacts/evidence/phase-011-offline-dependencies.txt` | PASS using the current machine's uv cache |
| Fast gate from recreated environment, offline | `uv run --offline --locked --no-sync --python 3.13 python scripts/check_fast.py` | 0 | `artifacts/evidence/phase-011-offline-dependencies.txt` | PASS |

This proves that the committed lock can be recreated without network access from the cache present on this machine. It does not prove a cold-cache install on an arbitrary machine. The earlier phase 010 service-gate failure was caused by missing PostgreSQL DSN/services and is not evidence of an offline package-cache failure.
