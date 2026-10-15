# P04 local package provenance

## Current artifact

- Distribution: `supportops-async` version `0.1.2`.
- Artifact: `supportops_async-0.1.2-py3-none-any.whl`.
- Source commit: `3aa96ec9d3fa2f85f771d9b5aaa4c5ab3641034d` (`build(p04): prepare async package 0.1.2`).
- SHA-256, Python range, supported FastAPI range, direct dependency versions, and dependency lock hash: `artifact.lock.json`.
- Tested resolution: FastAPI 0.142.4 and OpenTelemetry API 1.45.1. The library does not configure telemetry exporters.
- Compatibility tests: FastAPI 0.137.1 and 0.142.4 each passed the API and full local unit/recovery suite. Evidence is under `artifacts/evidence/fastapi-compat-*.txt`.
- Build: `uv build --offline --out-dir artifacts/packages .`; exit 0. Output: `artifacts/evidence/p04-012-wheel-build.txt`.
- Offline install: wheel installed with `--no-index --no-deps --target`; isolated smoke verified imports originate in the installed wheel, wheel metadata, FastAPI 0.142.4, migration data, API route, and task completion. Output: `artifacts/evidence/p04-012-wheel-install.txt` and `p04-012-wheel-consumer.txt`.
- No external publication. This wheel is retained in P04 local Git for explicit consumer approval.

## Historical artifact

The previous `supportops-async` 0.1.0 and 0.1.1 wheels and their provenance remain in local Git. Version 0.1.2 is the current consumer artifact.
