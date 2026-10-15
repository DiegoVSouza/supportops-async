# Plan — API and store

## allowed_write_paths
- `supportops_async/api/**`, `supportops_async/store/**`
- `tests/api/**`, `tests/store/**`, `openapi.yaml`
- `artifacts/**`, `docs/**`, `pyproject.toml`, `uv.lock`, `Makefile`

## forbidden_changes
- Kit, lab root, sibling projects, cloud deployment, real side effects.

## Tasks
1. Freeze request/response schemas and task state transitions.
2. Implement repository protocol plus transactional idempotency store.
3. Add FastAPI routes and contract/failure tests.
4. Add migration and local Postgres integration checks; record unavailable-service limitations.

## Check and stop
Unit: `uv run pytest -q tests/api tests/store`; integration: `uv run pytest -m integration`. Stop if route/schema change is needed; create ADR first.
