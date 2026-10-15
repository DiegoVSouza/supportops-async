# P04 local package provenance

- Distribution: `supportops-async` version `0.1.0`.
- Artifact: `supportops_async-0.1.0-py3-none-any.whl`.
- Source commit: `d66bf316eedb2a5a810bc0a35ebf80d37f4474ab` (`feat(platform): add local async runtime and service stack`).
- SHA-256 and direct dependency versions: `artifact.lock.json`.
- Dependency lock: project `uv.lock`; its SHA-256 is included in `artifact.lock.json`.
- Build: `uv build --wheel --out-dir artifacts/packages`; exit 0. Output is saved in `artifacts/evidence/package-build.txt`.
- Local offline wheel installation: `uv pip install --offline --no-deps --python artifacts/packages/.venv/Scripts/python.exe artifacts/packages/supportops_async-0.1.0-py3-none-any.whl`; exit 0.
- Smoke: isolated `python -I -S` imported the API, SQLite store, broker, worker, and packaged PostgreSQL migration from the installed wheel; a task completed with status `done`. Evidence: `artifacts/evidence/package-smoke-install.txt`.
- Limitation: a full dependency-resolving offline install was attempted and exited 1 because the uv offline resolver could not obtain `psycopg-binary==3.2.10` from its cache. The smoke supplied the exact dependencies already installed by this project's `uv.lock`; it proves the local wheel and its runtime path, not a self-contained offline dependency bundle.
- Publication: none. The wheel is retained only in this project's local Git repository.
