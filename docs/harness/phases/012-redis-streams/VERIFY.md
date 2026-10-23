# VERIFY — Redis Streams broker

Status: PASS_LOCAL_SERVICES.

| Gate | Command | Exit | Evidence | Result |
| --- | --- | ---: | --- | --- |
| Fast gate and locked dependency metadata | `uv lock --check`; `uv run --locked python scripts/check_fast.py` | 0 | `artifacts/evidence/phase-012-full-gate.txt` | PASS |
| Redis Streams retry, worker recovery, attempts and DLQ | `P04_TEST_REDIS_URL=redis://127.0.0.1:16379/0 uv run --locked pytest tests/queue/test_redis_broker.py -q` | 0 | `artifacts/evidence/phase-012-full-gate.txt` | PASS against Redis 7.4.2 |
| Unit/subprocess, PostgreSQL/SQS scenarios, image and Terraform local plan | `P04_POSTGRES_DSN=... P04_LOCALSTACK_ENDPOINT=... P04_TEST_REDIS_URL=... uv run --locked python scripts/check_full.py` | 0 | `artifacts/evidence/phase-012-full-gate.txt` | 32 tests passed; no Terraform apply |
| Wheel 0.1.4 | `uv build --offline --wheel`; isolated `uv pip install --offline --no-deps`; `python -I -S scripts/package_smoke.py --expected-version 0.1.4` | 0 | `artifacts/evidence/phase-012-wheel-{build,install,consumer}.txt`; `artifacts/packages/provenance-0.1.4.md` | PASS |
