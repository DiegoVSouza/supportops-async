# Verify — API and store

- [x] POST returns 202 and stable task ID; same key returns same ID; conflicting payload behavior is explicit.
- [x] GET exposes only defined statuses and progress; queued/retrying/running cancellation is cooperative and bounded to step boundaries.
- [x] Conflicting body with the same idempotency key returns the original task and does not replace its payload.
- [x] Unit contract/failure tests pass; PostgreSQL integration remains separately INCOMPLETE.
- [x] Save command, exit code, and output in `artifacts/evidence/`.
