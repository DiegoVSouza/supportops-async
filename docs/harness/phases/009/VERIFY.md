# VERIFY — Service process recovery

| Layer | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Real PostgreSQL/SQS kill-after-commit recovery | uv run --locked pytest tests/integration/test_service_crash_recovery.py -q -s | 0 | artifacts/evidence/phase-009-crash-recovery.txt | PASS after lease expiry |
| Unit/service, long-step/duplicate/retry/DLQ, image and Terraform init/validate/plan | uv run --locked python scripts/check_full.py | 0 | artifacts/evidence/phase-009-full-gate.txt | PASS; no apply |
| Early redelivery before lease expiry | New defect found; phase 010 required | — | worker claim branch | INCOMPLETE |
