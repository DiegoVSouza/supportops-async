# Verify — Durability

- [x] Crash after checkpoint resumes at the next step (actual subprocess exit and SQLite reopen).
- [x] Crash around committed fake effect does not duplicate the effect (actual subprocess exit and SQLite ledger).
- [x] Duplicate queue delivery and repeated HTTP creation preserve one task/effect (unit/contract tests).
- [x] Create/completed/failed lifecycle events use a durable outbox; failed event publication remains pending (SQLite tests).
- [x] Save actual subprocess output; it is explicitly a SQLite subprocess test and does not represent PostgreSQL/SQS full-stack recovery.
