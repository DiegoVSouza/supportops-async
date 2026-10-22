# PLAN — Complete remaining authorized local remediation

allowed_write_paths: tests/**; scripts/**; artifacts/evidence/**; docs/**; .github/workflows/**; README.md; README.pt-BR.md

forbidden_changes: root roadmap, sibling source imports, shared kit changes, unrelated preexisting files/stacks, test weakening, external deploy/publish/push/PR/merge, Terraform apply, live/paid LLM.

llm_mode: fake

dependencies: Docker daemon and isolated local PostgreSQL/pgvector, Redis, LocalStack, Prometheus/Grafana/Jaeger/OTel; existing locked tools and approved P00–P04 wheels. Verify variable APIs in official docs and sources.lock.json.

## Observable tasks
1. Add a real subprocess crash scenario using PostgreSQL and SQS with isolated queues.
2. Integrate the scenario into required service checks and repair evidence scripts if inspection reveals defects.
3. Execute recovery, retry/DLQ, unit and full gates; reconcile evidence/state.

## Checks
Fast gate before each commit; meaningful red/green tests for changed behavior; unit/contract, package integration, service integration and E2E evidence separately; full gate and staged diff/secret review. Clean-context final verification follows the configured Builder review.

## Stop condition
Stop only the affected check for an unavailable dependency and save INCOMPLETE evidence; continue independent implementation. Leave cassettes/live/external-identity acceptance PENDING/INCOMPLETE. Do not claim external exactly-once from the local ledger.

## Plan review
Reviewed before code: four or fewer observable tasks; owned paths and package boundaries explicit; real-service and negative authorization checks included; public changes scoped in ADR; no missing gate can silently pass.
