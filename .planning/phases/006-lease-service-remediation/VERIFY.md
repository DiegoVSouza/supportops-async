# Verify — Phase 006: Lease and service-backed durability remediation

## Required truths and checks
1. Long-running steps retain/renew task lease and broker visibility beyond their intervals, without concurrent ownership or duplicate effect — targeted renewal tests, then `uv run pytest -q`.
2. PostgreSQL/LocalStack exercise crash recovery, bounded retry, DLQ, duplicate delivery, and effect idempotency — `uv run pytest -q -m service` with dependencies running.
3. Compose configuration and runtime are checked — `docker compose -f docker-compose.async.yml config` and documented service smoke.
4. Image builds with non-root runtime — `docker build -f Dockerfile -t supportops-async:local .` and inspect configured runtime user.
5. Terraform validates and produces a non-applying plan — `terraform -chdir=infra validate` and `terraform -chdir=infra plan`.
6. Required full gate fails closed when a mandatory check is missing or fails; the resulting status is accurately called INCOMPLETE/FAIL, never PASS.
7. Docs state at-least-once delivery and limit effect-ledger deduplication to tracked keys; feature list and progress cite evidence, while model quality/cost stay PENDING.

## Evidence rules
For each executed check, save command, exit code, and stdout/stderr under `artifacts/evidence/`, classified as unit/contract, local recovery, service integration, infrastructure, or full gate. If an executable/service is absent, save the attempted command and diagnostic and mark that gate INCOMPLETE. Do not fabricate a successful run.

## Result (filled during execution)
- [ ] 1: INCOMPLETE — implementation/check evidence pending.
- [ ] 2: INCOMPLETE — service availability and run pending.
- [ ] 3: INCOMPLETE — runtime gate pending.
- [ ] 4: INCOMPLETE — Docker build pending.
- [ ] 5: INCOMPLETE — Terraform CLI/gate pending.
- [ ] 6: INCOMPLETE — full remediation gate pending.
- [ ] 7: INCOMPLETE — docs/state reconciliation pending.
