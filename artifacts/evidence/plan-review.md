# P04 plan review

- Command: `git rev-parse --show-toplevel; git branch --show-current; git status --short`
- Exit code: `0`
- Output: `C:/estudo/Golpe/lab/projects/p04`; `main`; clean working tree.
- Review: accepted for execution. The four phases preserve the original API, idempotency, broker, retries/DLQ, checkpoints/crash recovery, local infrastructure, CI, and bilingual knowledge criteria. Each plan names owned paths, observable tasks, validation commands, and stop conditions.
- Scope note: SQLite and in-memory broker tests are unit/contract doubles only. PostgreSQL and LocalStack integration and a real process-crash recovery gate remain separate and must be reported INCOMPLETE when unavailable. Terraform is unavailable in the current environment and its validation must remain INCOMPLETE.
- Dependencies: no sibling source imports; any later P00/P01/P02/P03 integration requires approved versioned artifacts with source commit and SHA-256.
- Environment checks: Python 3.13.12, uv 0.12.7, Docker 29.1.3, Docker Compose 5.0.1; Terraform command unavailable. Installed FastAPI 0.135.1 / pytest 9.0.2 / httpx 0.28.1 are not assumed as locked dependencies.
- Stop conditions: public contract change requires ADR and versioned consumer update; unavailable external/local services are recorded INCOMPLETE, never simulated as integration PASS.
