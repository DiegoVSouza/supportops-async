# SPEC — PostgreSQL and SQS recovery service gates

## Objective
Use existing P04 remediation commit and isolated Compose services to prove PostgreSQL/LocalStack idempotency, retry/recovery and DLQ behavior for steps longer than lease/visibility intervals where implementation supports it.

## Acceptance
- Every executed gate records exact command, exit code, and output in rtifacts/evidence/.
- PASS applies only to the named layer; skipped/unavailable gates are INCOMPLETE and model evaluation without cassettes is PENDING.
- No project product code changes are planned in this evidence-first phase unless a concrete defect is found and separately scoped.
