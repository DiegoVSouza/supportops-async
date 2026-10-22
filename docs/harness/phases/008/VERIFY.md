# VERIFY — PostgreSQL and SQS recovery service gates

## Verification record

| Layer / requirement | Command | Exit code | Evidence path | Status |
| --- | --- | ---: | --- | --- |
| PostgreSQL idempotency + LocalStack SQS smoke | `uv run --locked pytest tests/integration -q` with P04 service env | 0 | `artifacts/evidence/phase-008-service-tests-rerun.txt` | PASS |
| Long step > 30 s lease, heartbeat, competing claim | `python artifacts/evidence/phase-008-service-scenarios.py` with P04 service env | 0 | `artifacts/evidence/phase-008-service-scenarios.txt` | PASS |
| Duplicate SQS delivery and effect ledger | same scenario command | 0 | `artifacts/evidence/phase-008-service-scenarios.txt` | PASS (local effect record only) |
| Bounded retry and DLQ at attempt 3 | same scenario command | 0 | `artifacts/evidence/phase-008-service-scenarios.txt` | PASS |
| Unit, Compose, image, Terraform init/validate/plan | `$env:P04_POSTGRES_DSN=<local DSN>; $env:P04_LOCALSTACK_ENDPOINT=http://127.0.0.1:14566; python scripts/check_full.py` | 0 | `artifacts/evidence/phase-008-full-gate-rerun-summary.txt; artifacts/evidence/phase-008-full-gate-rerun.txt` | PASS; no apply |
| Service worker crash after committed effect | Not simulated against PostgreSQL/SQS | — | `artifacts/evidence/phase-008-service-scenarios.txt` | INCOMPLETE |

## Review checklist
- [x] Exact commands, exit codes, and output are saved.
- [x] Service-backed evidence identifies PostgreSQL 17.11 and LocalStack 4.14.0.
- [x] No Terraform apply or external deployment occurred.
- [x] Feature/progress/knowledge docs retain the service crash-recovery limitation.
- [x] Staged changes are limited to phase evidence/state/docs and contain no credentials.
