# Verify — Bounded campaign ledger for P04

Record exact commands, exits, and sanitized outputs in `artifacts/evidence/live-campaign-ledger/`.

- [x] Reservation and result journal is append-only; missing usage retains its reservation; completed/uncertain attempts cannot be rerun.
- [x] Cumulative requests/tokens/cost are atomic across campaigns and concurrent processes.
- [x] OS lease blocks a second P04 campaign and releases normally; metadata contains no task content or secret.
- [x] Resume is read-only, sanitized, rejects unknown/empty campaigns with exit 2, and never dispatches.
- [x] Dry-run and blocked generation do not contact Groq, inspect credentials, invoke Docker/services, or perform effects/refunds.
- [x] Focused tests pass (6 ledger, 11 preparation); full gate has 60 passing tests and 4 service skips, then reports `INCOMPLETE` because PostgreSQL/LocalStack/Docker/Terraform services were isolated.
- [x] Historic live evidence and stacks are unchanged; decisions, failures, progress, evidence, and bilingual knowledge are updated.
- [ ] Staged diff is reviewed and committed locally; clean-context review remains separately recorded.

This phase does not pass the service live gate. PostgreSQL/SQS/Redis workflow behavior, crash boundaries, model quality, authorized quota, canary, and rollback remain outstanding.
