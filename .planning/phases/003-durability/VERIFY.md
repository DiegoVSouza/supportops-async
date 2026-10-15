# Verify — Durability

- [ ] Crash after checkpoint resumes at the next step.
- [ ] Crash around effect boundary does not duplicate the effect.
- [ ] Duplicate queue delivery and repeated HTTP creation preserve one task/effect.
- [ ] Create/completed/failed lifecycle events use a durable outbox; failed event publication remains pending.
- [ ] Save actual subprocess/database test output; no in-memory simulation is labeled real crash recovery.
