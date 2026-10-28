# Plan

1. Record Docker identities/states/images/volumes/networks, verify cached images, empty namespace p04-phase027 and free loopback ports 35432/34566/36379 (initial 24566/26379 were occupied; no service started). Create a dedicated Compose stack and phase-owned Terraform copy/config.
2. Run the locked fake full gate including the OTLP wire test and service recovery, unique image supportops-async:phase027, Terraform init/validate/plan only through explicit network p04-phase027-local. Reuse phase025's bridge/loopback pattern: the first internal-network attempt prevented Windows host access; no gateway is added. Set project PYTHONPATH for the existing pytest CLI import contract.
3. Capture owned container mount identities, clean only exact phase resources, reconcile baseline identities and record results.

allowed_write_paths: `.planning/phases/027-current-full-privacy-gate/**`, `artifacts/evidence/current-full-privacy-027/**`.
allowed_resources: compose project p04-phase027; network p04-phase027-local; its labeled volumes and containers; image supportops-async:phase027; read-only existing cached images/provider mirror. Never delete unrelated or unattributed volumes or alter existing stacks.
forbidden_changes: product source, prior evidence, actual secrets, model calls, public ports, Terraform apply, root policy, sibling code, new gateway/connectivity, approvals.

Fake only, USD 0. max_tries: 3 persisted per failure. Plan-check: self-assessment. Stop lifecycle if namespace/port/image/ownership checks fail; cleanup owned resources in finally. Existing approved local LocalStack network pattern is reused; no host gateway is inferred.
