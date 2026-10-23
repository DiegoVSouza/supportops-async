# SPEC — Add a persistent Redis Streams broker

Add a Redis Streams implementation of the existing `Broker` protocol with visibility renewal, recovery after worker loss, retry accounting and a dead-letter stream. Keep `SqsBroker` and the public task/API contracts compatible. Redis is a durable delivery transport; PostgreSQL remains the source of task state and idempotency.

Acceptance requires locked dependency and package provenance updates, deterministic contract tests and a real Redis service scenario covering publish/consume/ack, visibility renewal, reclaim after simulated worker loss, bounded retries and dead-letter delivery.
