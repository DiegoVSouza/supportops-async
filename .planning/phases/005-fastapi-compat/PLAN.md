# Plan — FastAPI consumer compatibility

## allowed_write_paths

- `.planning/phases/005-fastapi-compat/**`, `docs/decisions/**`, `docs/harness/**`, `README*`
- `pyproject.toml`, `uv.lock`, `docs/harness/sources.lock.json`
- `tests/api/**`, `tests/compat/**`, `scripts/**`
- `artifacts/evidence/**`, `artifacts/packages/**`

## forbidden_changes

No P05 edits, sibling imports, route/status/schema changes, external publication, deploy, or unapproved live service calls.

## Tasks

1. Record the consumer mismatch and test the API suite against FastAPI 0.142.4 and the prior supported endpoint 0.137.1.
2. Record an ADR, update the documented source and compatibility range, pin the lock to the tested release, and bump the package patch version.
3. Build the local wheel, verify metadata/hash/source provenance, and install/smoke it in an isolated environment.

## Validation and stop condition

Run the compatibility and full local unit/recovery tests, `uv lock --check`, artifact lock validation, and wheel smoke. Keep PostgreSQL/LocalStack and container gates INCOMPLETE. Stop if a public API behavior fails or a dependency cannot be resolved without changing another project's files.
