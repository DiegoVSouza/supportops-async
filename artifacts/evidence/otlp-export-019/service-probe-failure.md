# Controlled local service probe result

- Candidate commit: `d6cf5c9039e5dfd746331fda3f192e66e6e67184`.
- Requests: one synthetic `POST /tasks` with idempotency key `otlp-smoke-019`; no LLM/provider configured or called.
- Task ID: `ac52c679-8226-4658-9eca-6739e4caf906`.
- Deterministic trace ID: `4bf92f3577b34da6a3ce929d0e0e4736`.
- Task reached terminal success (`done`). Jaeger returned only `supportops.worker.process`; expected API span `supportops.api.request` was absent.
- API startup log included `Overriding of current TracerProvider is not allowed`.
- Outcome: FAIL for API+worker correlated OTLP export. Do not replay this semantic service probe. Preserve this trace/task identity and record the corrective implementation under a new candidate phase.
- Failed command: `uv run --locked python artifacts/evidence/otlp-export-019/service-probe.py`, exit 1.
