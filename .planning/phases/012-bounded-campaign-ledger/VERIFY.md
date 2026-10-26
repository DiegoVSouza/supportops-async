# Verify — Bounded campaign ledger for P04

Record exact commands, exits, and sanitized outputs in `artifacts/evidence/live-campaign-ledger/`.

- [ ] Reservation and result journal is append-only; missing usage retains its reservation; completed/uncertain attempts cannot be rerun.
- [ ] Cumulative requests/tokens/cost are atomic across campaigns and concurrent processes.
- [ ] OS lease blocks a second P04 campaign and releases normally; metadata contains no task content or secret.
- [ ] Resume is read-only, sanitized, rejects unknown/empty campaigns with exit 2, and never dispatches.
- [ ] Dry-run and blocked generation do not contact Groq, inspect credentials, invoke Docker/services, or perform effects/refunds.
- [ ] Focused tests and deterministic gates pass; any skipped service/full checks are labeled `INCOMPLETE` with their reason.
- [ ] Historic live evidence and stacks are unchanged; decisions, failures, progress, evidence, and bilingual knowledge are updated.
- [ ] Staged diff is reviewed and committed locally; clean-context review remains separately recorded.

This phase does not pass the service live gate. PostgreSQL/SQS/Redis workflow behavior, crash boundaries, model quality, authorized quota, canary, and rollback remain outstanding.
