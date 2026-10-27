# Phase 019 verification

## Status

**INCOMPLETE.** Dependency lock, opt-in wiring, focused privacy checks, fast gate, offline suite, unique image build, and Compose lifecycle passed. The actual service probe failed the API span criterion: the task completed, and Jaeger received only the worker span for the trace. Do not replay that semantic service probe.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Plan check | PASS | `artifacts/evidence/otlp-export-019/plan-check.json` |
| Fast gate | PASS | `check-fast.txt` |
| Offline tests | PASS: 75 passed, 4 skipped | `offline-pytest.txt` |
| Candidate image build | PASS | `image-build.txt`; immutable tag `supportops-async:phase019` |
| Compose config/start | PASS | `compose.override.yml`, `compose-up.txt` |
| API + worker trace in Jaeger | FAIL | `service-probe-failure.md`, `service-probe.txt` |
| Phase cleanup | PASS | `compose-down.txt`; phase containers/network/volumes removed |
| Human/independent/release reviews | PENDING | Not performed |

## Trace identity and failure preservation

Candidate commit: `d6cf5c9039e5dfd746331fda3f192e66e6e67184`.
One synthetic local request created task `ac52c679-8226-4658-9eca-6739e4caf906` with deterministic trace `4bf92f3577b34da6a3ce929d0e0e4736`. The task reached `done`. Jaeger returned `supportops.worker.process` but not `supportops.api.request`; the API startup log contained `Overriding of current TracerProvider is not allowed`. Preserve this event and identity. Correct setup in a new candidate phase; no LLM/provider request occurred.

No external listener or cloud resource was used. Previous `supportops-async:local-check` image remains `sha256:5cc87bb6e992903af9b4a5dfa2c6e4a14a2d6d6a28f8a7fa37dfc34c8354e505`; phase image is `sha256:d242bc9bd74d07974a9a4adf60e9cb1c67a3824b2d4e815eb8422643b26cf6bb`.
