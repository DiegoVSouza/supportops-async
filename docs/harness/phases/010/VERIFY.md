# VERIFY — Early redelivery

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Early redelivery regression | uv run --locked pytest tests/worker/test_early_redelivery.py -q | 1 then 0 | artifacts/evidence/phase-010-early-redelivery-red.txt; phase-010-early-redelivery-green.txt | PASS red/green |
| Full unit/service recovery, long-step/DLQ, image, Terraform init/validate/plan | uv run --locked python scripts/check_full.py | 0 | artifacts/evidence/phase-010-full-gate.txt | PASS; no apply |
| First full attempt with services stopped | same full gate | 1 | artifacts/evidence/phase-010-full-gate-services-unavailable.txt | INCOMPLETE environment, retained |
| Versioned 0.1.3 wheel | uv build --offline --wheel; isolated install and package_smoke --expected-version 0.1.3 | 0 | artifacts/evidence/phase-010-wheel-build.txt; phase-010-wheel-install.txt; phase-010-wheel-consumer.txt | PASS |
