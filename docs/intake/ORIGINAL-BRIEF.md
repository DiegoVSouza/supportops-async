# Original P04 brief

Source: `specs/P04-async-ai-platform.md` in the lab curriculum. The project is independently versioned; all former monorepo paths map under this repository. P00/P01 integrations remain versioned package dependencies and are not loaded by relative sibling paths.

## Preserved goals and acceptance
- FastAPI POST/GET/cancel task endpoints; `Idempotency-Key` returns the same task ID.
- Broker protocol and SQS/SNS implementation for LocalStack; durable worker with heartbeat, retry/backoff, DLQ, idempotency and checkpoints.
- Crash recovery resumes without duplicate simulated effects; duplicate delivery results in one effect; permanent failure reaches DLQ.
- Local compose, non-root multi-stage Docker, Terraform plan only, and CI build/test. Image push and deployment remain unauthorized.
- Document at-least-once delivery and recovery. No cloud deployment, auth, RAG, or advanced tracing.
