# Validation categories

- Unit and contract behavior: `unit-tests.txt` — SQLite, in-memory broker, FastAPI ASGI transport, and event inbox tests; 24 passed. These doubles are not service integration.
- Process recovery: `subprocess-recovery.txt` — one real child process exits with `os._exit(23)` after a committed effect; a new worker reopens SQLite after lease expiry. This is local process recovery, not full-stack E2E.
- Service integration: `integration-tests.txt` — PostgreSQL and LocalStack tests are skipped because endpoints are not configured. Status INCOMPLETE.
- Full available gate: `check-full.txt` — unit plus process recovery pass; Compose configuration passes; PostgreSQL, LocalStack, Docker image build, and Terraform gates remain INCOMPLETE.
- Agent/model evaluation: not run; there is no live LLM evaluation, so model quality/cost metrics are PENDING.
