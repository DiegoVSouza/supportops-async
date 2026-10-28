# Plan

1. Add explicit offline Terraform mirror, workspace, network and endpoint settings to the gate, rejecting incomplete settings and removing automatic host gateway rewriting.
2. Run locked fast and full fake checks against a uniquely owned PostgreSQL/Redis/LocalStack stack and internal Terraform network; record commands, exits and output, no apply.
3. Capture mounts before cleanup and reconcile containers, networks and volumes. Preserve the historical unattributed volume; document that attribution cannot be reconstructed from existing evidence.

allowed_write_paths: `.planning/phases/025-offline-full-gate/**`, `scripts/check_full.py`, `artifacts/evidence/offline-full-gate-025/**`, `docs/harness/progress.md`. forbidden_changes: historical evidence, existing Terraform files/state, existing Docker resources, secrets, provider model calls, apply, public listeners, gateway assumptions and approvals. USD 0, fake only. Stop on failed validation, uncertain resource ownership or unexpected effects. Planning check is self-assessment; independent review PENDING.
