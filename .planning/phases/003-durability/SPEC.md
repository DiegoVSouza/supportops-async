# Phase 003 — Checkpoints and crash recovery

## Goal and acceptance
Persist step checkpoints and effect idempotency so a second worker resumes after a crash and does not repeat a completed effect. A real process-crash test must verify recovery; mocks alone do not satisfy this phase gate.
