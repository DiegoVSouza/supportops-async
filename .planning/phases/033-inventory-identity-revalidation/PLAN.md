# Plan

1. Inspect all phase032 Docker/service baselines and relevant earlier baseline records, Docker metadata/events and gate timestamps. Record observed identity and status differences, uncollected and unrecoverable fields. Check process/root `.env` key discovery without revealing values.
2. Implement and test stable identity comparison in phase-owned validation tooling, retaining meaningful detection of replacement, removal and foreign-resource changes. Prepare a fresh snapshot, unique namespace/image/ports and explicit inventories. Preserve the protected existing check-full output.
3. Execute exactly one additional full fake service gate in the fresh snapshot after readiness passes, persist the attempt before execution and preserve historical3/3. Reconcile only owned resources and record the result; never dispatch live P04 automatically. Inspect the distinct operation032 authority and frozen bindings separately before any live dispatch.

allowed_write_paths: `.planning/phases/033-inventory-identity-revalidation/**`, `scripts/docker_inventory_identity.py`, `tests/test_docker_inventory_identity.py`, `scripts/credential_presence.py`, `tests/test_credential_presence.py`, `artifacts/evidence/inventory-revalidation-033/**`, `docs/harness/progress.md`.

forbidden_changes: phase032 reports/attempts, `gossett_backend` and all unrelated containers, images, networks and volumes; policy/ledgers/reservations; user-modified outputs; provider calls, live operation, customer data, fallback, paid use, Terraform apply, external effects, holdout or human-review claims.

Fake mode, paidUSD0, provider calls0. One additional full gate total; no rerun after FAIL. The gate may create only an inventoried unique namespace and image, with cleanup limited to resources whose ownership is proven. Stop on insufficient Docker/image/port isolation, uncertain ownership, inaccessible baseline or failed preparation. Plan-check is implementer self-assessment.
