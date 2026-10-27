# Phase 020 verification

## Status

INCOMPLETE until provider adoption tests, locked fast/offline/full gates, a new real local API+worker correlated OTLP trace, resource reconciliation, and evidence review pass.

## Gate boundaries

- Service export PASS requires one new synthetic API request whose API and worker spans are visible in Jaeger under one new trace ID.
- Never rerun the failed phase-019 key/trace; never send a provider/model request.
- A successful local tracing probe does not establish product quality, model billing, RAG readiness, human review, independent review, or promotion.

## Evidence

`artifacts/evidence/otel-provider-020/`
