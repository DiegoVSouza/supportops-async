# Plan

1. Capture existing container/network/volume identities and states, confirm cached images, free phase ports and an empty unique namespace.
2. Start only the three phase-owned dependencies, run locked service tests and recovery scenarios once, preserve command/output/exit evidence, clean the exact namespace and reconcile identities and states.

allowed_write_paths: `.planning/phases/022-current-service-scenarios/**`, `artifacts/evidence/current-service-scenarios-022/**`, `docs/harness/progress.md`. forbidden_changes: source, previous evidence, existing Docker resources, images/tags, provider access, credentials, data from customers, bridge assumptions, model quality and approvals.

Fake mode, USD 0, no provider calls. Validation: `uv run --locked --offline python scripts/check_fast.py`, focused service tests and `scripts/service_scenarios.py`; complete gate remains INCOMPLETE if Terraform native or independently planned bridge is unavailable. Stop on preflight mismatch, unexpected resource use, scenario failure or uncertain work. Plan-check self-assessment; independent review PENDING.
