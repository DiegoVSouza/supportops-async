# Verify — API and store

- [ ] POST returns 202 and stable task ID; same key returns same ID; conflicting payload behavior is explicit.
- [ ] GET exposes only defined statuses and progress; cancel follows allowed transitions.
- [ ] Unit contract/failure tests pass; Postgres integration is separately reported PASS or INCOMPLETE.
- [ ] Save command, exit code, and output in `artifacts/evidence/`.
