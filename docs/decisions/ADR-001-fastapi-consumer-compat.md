# ADR-001: Support the P05 FastAPI version

- Status: Accepted
- Date: 2026-10-15

## Context

The local `supportops-async` 0.1.0 wheel requires exactly FastAPI 0.137.1, while P05 pins 0.142.4. P05 correctly installed the approved wheel with `--no-deps` and marked the integration incomplete because these constraints conflict. P04's public API uses FastAPI's stable `FastAPI`, `Header`, `HTTPException`, `Response`, status, and Pydantic model APIs.

FastAPI's official release notes show 0.142.0 added native OpenTelemetry support and changed automatic exporter setup to require opt-in; 0.142.4 contains a telemetry isolation fix. P04 does not configure automatic telemetry/exporters. FastAPI 0.142.4 declares `opentelemetry-api>=1.44.0` as a runtime dependency, which must be resolved and locked rather than bypassed.

## Decision

Set P04's supported FastAPI interval to `>=0.142.4,<0.143.0`, lock the tested resolver result, and publish the next patch package version, 0.1.1. This range includes the P05-pinned version while avoiding an untested next minor release. No route, status, schema, or response behavior changes.

## Evidence

- Official [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/) list changes for 0.142.0 and 0.142.4.
- Official [FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/) and [async tests documentation](https://fastapi.tiangolo.com/advanced/async-tests/) describe the supported ASGI testing approach used by P04.
- `artifacts/evidence/fastapi-compat-api-tests.txt`: API contract tests pass on FastAPI 0.142.4.
- `artifacts/evidence/fastapi-compat-full-tests.txt`: all 25 local unit/recovery tests pass on FastAPI 0.142.4; two service integrations are deliberately deselected.

## Consequences

- Consumers using FastAPI 0.137.1 must upgrade to 0.142.4 or a compatible 0.142.x release when moving to P04 package 0.1.1.
- The lock now includes FastAPI's required OpenTelemetry API dependency. P04 does not enable telemetry or make telemetry exporter calls.
- PostgreSQL/LocalStack integration remains INCOMPLETE until those services are available; FastAPI compatibility tests do not approve service integration.
