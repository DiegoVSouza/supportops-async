# P04 0.1.2 source commit checks

- `uv lock --offline` — exit 0; updated the project lock from 0.1.1 to 0.1.2.
- `uv run --locked pytest -q -rs --basetemp artifacts/evidence/.pytest-tmp/p04-012-source tests` — exit 0; 27 passed, 2 skipped because PostgreSQL and LocalStack endpoints are unset. Output in `p04-012-source-tests-local-temp.txt`.
- `uv run python scripts/check_fast.py` — exit 1 because the existing 0.1.1 artifact provenance lock still binds the previous `uv.lock` SHA-256. This is expected during the two-commit release step; the new wheel lock and consumer smoke will be recorded after the source commit. Output in `p04-012-source-fast-check.txt`.
