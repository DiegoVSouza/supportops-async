# PLAN — PostgreSQL and SQS recovery service gates

## Allowed write paths
artifacts/evidence/**; docs/harness/**; docs/harness/phases/008/**; docs/knowledge/P04-async.md; README.md; README.pt-BR.md; tests/** and supportops_async/** only if a reproducible defect is found, then separate implementation task

## Forbidden changes
No terraform apply, external deployment/publication, push, unrelated stacks, no changes to shared kit/other repos, no weakened tests, no root roadmap.

## Dependencies
Docker CLI/daemon; isolated docker-compose.remediation.yml services with loopback ports 15432/14566/18000; Terraform plan only.

## Observable tasks
`n- 1. Review commit 1d919a2 and prior evidence; start isolated services. `n- 2. Run PostgreSQL/SQS service scenarios and save each command result. `n- 3. Run permitted configuration/full gates. `n- 4. Reconcile states and docs from evidence.

## Checks
Existing full gate; PostgreSQL and LocalStack service tests; explicit long-step lease/recovery, idempotency, bounded retry/DLQ tests; Compose/image/Terraform gates if not already evidenced.

## Stop condition
Do not claim PostgreSQL/SQS behavior unless executed against those services. Record implementation gaps as INCOMPLETE and do not apply Terraform.

## Review
Plan reviewed before execution: scope is evidence-first, tasks are observable, path ownership is explicit, and unavailable services cannot become PASS.
