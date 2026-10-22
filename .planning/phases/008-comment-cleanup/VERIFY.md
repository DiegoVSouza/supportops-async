# Verify

Run `python scripts/check_fast.py` and compare Python tokens against HEAD with comments excluded. Save commands, output, and exit codes under `artifacts/evidence/`.

The initial full gate exited 2 because service environment variables were absent; see `artifacts/evidence/comment-cleanup-full.txt`.

With `LLM_MODE=fake`, `P04_POSTGRES_DSN` set to the local P04 PostgreSQL instance on port 15432, and `P04_LOCALSTACK_ENDPOINT=http://127.0.0.1:14566`, `.venv\Scripts\python.exe -u scripts/check_full.py` exited 0. The run passed 31 tests, service scenarios, image build, and Terraform validation and local plan. Output: `artifacts/evidence/comment-cleanup-services.txt`.
