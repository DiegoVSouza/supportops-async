# Plan

1. Create a phase-owned Terraform CLI mirror configuration using the cached provider and a copy of the locked configuration.
2. Run init and validate with network disabled; retain command, directory, exit and output.

allowed_write_paths: `.planning/phases/024-offline-provider/**`, `artifacts/evidence/offline-provider-024/**`. forbidden_changes: existing Terraform configuration/state, historical evidence, credentials, provider model calls, apply and unrelated Docker resources. Budget USD 0. Stop on missing provider, checksum mismatch or failure. Self-assessed plan-check; independent review pending.
