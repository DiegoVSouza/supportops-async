# P04 live-v1 plan and worker rubric

## Scope

Evaluate the allowlisted plan, durable worker/API contracts, and recovery behavior. The future live target is the actual local API/worker stack backed by PostgreSQL, LocalStack SQS, and Redis Streams. SQLite and in-memory broker demonstrations do not satisfy service acceptance. All task/effect inputs are synthetic. Real refund calls, external writes, cloud deployment, and customer data are prohibited.

## Critical dimensions

1. **Plan validity and step quality:** accept only the expected allowlisted order; reject empty, duplicate, reversed, malformed, or over-limit steps before effects.
2. **Cancellation and authorization:** no new effect may commit after cancellation or authorization expiry. Any already committed effect is reported accurately.
3. **Duplicates and retries:** each task/step idempotency key maps to at most one durable simulated effect. Transient failures follow the configured bounded retry; permanent failures terminate and reach the DLQ.
4. **Lease and crash recovery:** competing workers cannot act while a valid lease is held. Recovery waits for expiry and resumes from durable checkpoints. Crashes before provider response, after provider response but before effect commit, and after effect commit are distinct outcomes.
5. **Provider response versus effect commit:** record separately whether a response arrived and whether an effect committed. Provider billing may be repeated or unknown after crashes; never assert exactly-once billing.

A case passes only when every critical assertion passes. Report errors by family, language, split, and error type; preserve failures. A holdout-driven change requires a newly authorized and reviewed confirmation set before claiming generalization.
