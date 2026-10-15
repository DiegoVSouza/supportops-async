# ADR-001: Support the P05 FastAPI version

- Status: Accepted
- Date: 2026-10-15

## Context

The local `supportops-async` 0.1.0 wheel requires exactly FastAPI 0.137.1, while P05 pins 0.142.4. P05 correctly installed the approved wheel with `--no-deps` and marked the integration incomplete because these constraints conflict. P04's public API uses FastAPI's stable `FastAPI`, `Header`, `HTTPException`, `Response`, status, and Pydantic model APIs.

FastAPI's official release notes show 0.142.0 added native OpenTelemetry support and changed automatic exporter setup to require opt-in; 0.142.4 contains a telemetry isolation fix. P04 does not configure automatic telemetry/exporters. FastAPI 0.142.4 declares `opentelemetry-api>=1.44.0` as a runtime dependency, which must be resolved and locked rather than bypassed.

## Decision

Set P04's supported FastAPI interval to `>=0.137.1,<0.143.0`, lock FastAPI 0.142.4 with `opentelemetry-api` 1.45.1, and publish the next patch package version, 0.1.1. The API suite passed on both range endpoints (0.137.1 and 0.142.4); the upper bound avoids an untested next minor release. No route, status, schema, or response behavior changes.

## Evidence

- Official [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/) list changes for 0.142.0 and 0.142.4.
- Official [FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/) and [async tests documentation](https://fastapi.tiangolo.com/advanced/async-tests/) describe the supported ASGI testing approach used by P04.
- Official [OpenTelemetry Python release notes](https://github.com/open-telemetry/opentelemetry-python/releases) identify the locked `opentelemetry-api` 1.45.1 release.
- `artifacts/evidence/fastapi-compat-api-tests.txt`: API contract tests pass on FastAPI 0.142.4.
- `artifacts/evidence/fastapi-compat-full-tests.txt`: all 25 local unit/recovery tests pass on FastAPI 0.142.4; two service integrations are deliberately deselected.
- `artifacts/evidence/fastapi-compat-0137-full-tests.txt`: all 25 local unit/recovery tests pass on the supported lower endpoint, FastAPI 0.137.1.
- `artifacts/evidence/fastapi-compat-locked-full-tests.txt`: all 25 local unit/recovery tests pass after `uv sync --locked --offline`; service integrations remain skipped.

## Consequences

- Consumers on FastAPI 0.137.1 remain supported; consumers on FastAPI 0.142.4 can now install P04 0.1.1 without bypassing dependency metadata.
- The lock resolves FastAPI's required OpenTelemetry API dependency to 1.45.1. P04 does not enable telemetry or make telemetry exporter calls.
- PostgreSQL/LocalStack integration remains INCOMPLETE until those services are available; FastAPI compatibility tests do not approve service integration.
