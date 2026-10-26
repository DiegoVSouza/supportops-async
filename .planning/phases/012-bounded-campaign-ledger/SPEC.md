# Phase 012 — Bounded campaign ledger for P04

## Goal

Add P04-local durable call reservations, cumulative campaign caps, a process lease, and read-only resume inspection. Keep broad campaign dispatch disabled until budget/quota, human review, service identity, and authenticated model preflight are evidenced.

## Starting evidence

- Phase 011 freezes 60 synthetic workflow cases (18 development / 42 holdout; 36 English / 24 Portuguese) and plans 18 pilot, 540 primary, 180 confirmation, or 738 additive calls.
- The live target is the actual API/worker backed by PostgreSQL, LocalStack SQS and Redis; SQLite/in-memory demo evidence does not satisfy service acceptance.
- P04 paid budget is USD 0. Free-tier quota, cumulative caps, confirmation capacity, independent review, service identity/ports, pacing, wall-clock cap, and model preflight remain pending.
- Existing single-workflow live evaluation is historical and does not authorize the expanded campaign.

## Acceptance criteria

1. Append-only SQLite journal reserves provider-call/token/cost ceilings before an attempt, reconciles known usage, retains unknown usage, and prevents retries of uncertain or completed trials.
2. Cumulative request/token/cost caps are transactionally enforced across P04 campaign IDs and concurrent reservations.
3. OS lease prevents concurrent P04 campaign processes and releases normally; metadata contains no task request, plan, reply, tool argument, or credential.
4. `--resume CAMPAIGN_ID --dry-run` is read-only, reports sanitized attempt and usage metadata, rejects unknown/empty campaign IDs with exit 2, and does not retry dispatched calls.
5. Dry-run and blocked execution do not access provider credentials/network, Docker services, real effects, or refund tools. Generation remains blocked while any authorization/resource prerequisite is pending.
6. Focused ledger and fake deterministic checks pass. Full check is run only with Docker hidden and services skipped to avoid building images or changing unrelated stacks; any skipped service/build gates stay explicitly `INCOMPLETE`.

## Out of scope

Groq dispatch, PostgreSQL/SQS/Redis/Docker service changes, worker crash-recovery implementation, real refunds/effects, budget or quota changes, dataset/rubric edits, cross-project accounting, deployment, or external effects.

## Status

`PLANNED`; campaign and service promotion remain `INCOMPLETE`.
