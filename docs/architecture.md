# Architecture

P04 exposes task submission and status through FastAPI, persists task state and idempotent step effects in SQLite or PostgreSQL, and delivers task IDs through in-memory, SQS, or Redis Streams brokers. Workers claim tasks under a store lease, renew broker visibility while running a step, checkpoint completed effects, and use bounded retry plus a dead-letter path. A transactional outbox records task lifecycle events.

Phase 016 propagates only W3C `traceparent` from the HTTP request through broker messages, retries, redelivery, and the worker step thread. Baggage, request headers, task IDs, payloads, and exception text are excluded from trace attributes. OTel API spans use bounded operation/status fields and fixed error categories. The project has no SDK exporter or collector configured, so delivery of traces to an external or local backend remains INCOMPLETE.

API and worker outer spans also disable OpenTelemetry's automatic exception status mutation. Explicit error handling sets a generic ERROR code and fixed error category, while the original exception propagates. In-memory regressions cover both actual call paths; production exporter privacy is not established by those tests.

P04 has no RAG runtime, owned retrieval source, corpus, or tenant retrieval contract. Retrieval behavior is INCOMPLETE pending a project-owned source and authorization protocol. The task workflow remains a deterministic local workflow; model planning is a separately recorded optional path.

External side effects cannot be made universally exactly once by the local effect ledger. A crash after a remote effect and before its local commit can repeat that effect unless the destination honors the same idempotency key or shares a transaction.
