# Phase 002 — Broker and worker

## Goal and acceptance
Implement `Broker` with LocalStack SQS/SNS and a worker that acknowledges, nacks with delay, retries with backoff, and routes terminal failures to DLQ. A duplicated message must not duplicate the simulated effect.
