# Phase 020 verification

## Status

**PASS for the P04 API-to-worker OTLP export gate and the local full gate.** The candidate was committed before any local service request and was not changed during verification. Human/release reviews remain PENDING, and this does not promote P04 or establish model quality, external provider billing, RAG readiness, or deployment safety.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Plan check | PASS | `artifacts/evidence/otel-provider-020/plan-check.json` |
| Candidate | `beff749202805b138d820daaddb80a4468afc7c9` | Local commit before service probe |
| Fast gate | PASS | `check-fast-final.txt` |
| Focused telemetry tests | PASS: 13 | `focused-telemetry.txt` |
| Complete offline tests | PASS: 80, 4 expected service skips | `offline-pytest-final.txt` |
| Unique candidate image build | PASS | `image-build.txt`; phase tag image ID `080d3dd8...` before service start |
| Isolated API+worker trace export | PASS | One task `d05d93a4-22a7-4d5d-a773-89b854cc0d7e`; trace `a18b72e4c9634d1f9a2b6c5d0e8f4712`; GET-only `trace-readback.txt` reports API and worker spans, correct service names, allowlisted scalar attributes, and no UUID-shaped attribute values |
| Full local gate | PASS, exit 0 | `full-gate.txt`: 84 tests; service lease/duplicate/retry-DLQ; unique image build; Terraform init/validate and LocalStack plan 6 add, 0 change, 0 destroy; no apply |
| Resource reconciliation | PASS | `inventory-reconciliation.txt`: exact pre/post 102 containers, 21 networks, 89 volumes; phase namespace removed |
| Prior image tags | PASS | `local-check` stayed `sha256:5cc87bb6...`; phase-019 stayed `sha256:d242bc9b...` |
| Paid/provider/model requests | 0 | No provider credentials read or provider/model calls |
| Human/independent/dataset/rubric/promotion approvals | PENDING | Not performed |

## Probe/tooling notes

The one-shot submit script completed the task but exited 1 while trying to create a set from Jaeger tag dictionaries (`TypeError: unhashable type: 'dict'`). The task was not resubmitted. A separate GET-only readback against the already stored trace then verified the full criterion successfully; its output and task/trace identity are retained. A later optional readback after the phase stack had already been shut down exited with connection refused and made no submission; it is not the primary trace evidence.

The full gate rebuilt the phase tag from the same committed source after the probe; this produced a new image identity (`9ccb86cd...`) while the source commit remained `beff749...`. The service probe ran on the pre-gate build (`080d3dd8...`). The `supportops-async:local-check` and phase-019 tags were unchanged.

## Limits

This is synthetic local service evidence only. It does not complete P04 RAG/retrieval, production deployment, live-model evaluation, human review, independent review, or promotion gates. Phase 019's initial failed event and trace remain immutable historical evidence and are superseded only for the current exporter implementation by this phase-020 candidate.
