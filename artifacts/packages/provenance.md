# P04 local package provenance

## Current artifact

- Distribution: `supportops-async` version `0.1.1`.
- Artifact: `supportops_async-0.1.1-py3-none-any.whl`.
- Source commit: `6a074e906b080fdb837907237787f623f17c3e3c` (`fix(compat): widen supported FastAPI range`).
- SHA-256, Python range, supported FastAPI range, direct dependency versions, and dependency lock hash: `artifact.lock.json`.
- Tested resolution: FastAPI 0.142.4 and OpenTelemetry API 1.45.1. The library does not configure telemetry exporters.
- Compatibility tests: FastAPI 0.137.1 and 0.142.4 each passed the API and full local unit/recovery suite. Evidence is under `artifacts/evidence/fastapi-compat-*.txt`.
- Build: `uv build --wheel --out-dir artifacts/packages`; exit 0. Output: `artifacts/evidence/fastapi-compat-package-build.txt`.
- Offline install: dependencies synchronized from `uv.lock` into an isolated environment, then this wheel was installed offline without dependency resolution. Smoke verified imports originate in the installed wheel, wheel metadata, FastAPI 0.142.4, migration data, API route, and task completion. Output: `artifacts/evidence/fastapi-compat-package-install.txt`.
- No external publication. This wheel is retained in P04 local Git for explicit consumer approval.

## Historical artifact

The previous `supportops-async` 0.1.0 wheel and its provenance are retained as `supportops_async-0.1.0-py3-none-any.whl`, `artifact-0.1.0.lock.json`, and `provenance-0.1.0.md`. Its FastAPI dependency was pinned to 0.137.1 and is not the artifact consumers should use for FastAPI 0.142.4.
