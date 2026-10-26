# Phase 011 — Live campaign preparation

## Goal

Prepare reviewed plan/worker scenarios, operational assertions, and a guarded reservation dry-run for P04's broad live-readiness evaluation. The live target is the documented API/worker service with real local PostgreSQL, SQS/LocalStack and Redis dependencies; the existing SQLite/in-memory Groq demo does not prove that service path.

## Current evidence and constraints

- Revalidated repository HEAD: `0f3566de677c60cbeebe0ad0e4b2f36856213d2f` (`feat(planner): evaluate real Groq steps over durable services`).
- The production worker remains provider-agnostic. Phase 013's single free-plan synthetic planner task is historical and does not authorize a campaign or paid usage. Project policy is zero paid LLM spend.
- Existing Docker/service evidence covers earlier local acceptance; recheck stack identity, ports, and dependencies before any later execution.
- No provider call, Docker mutation, real refund/effect, deployment, or change to production worker behavior is part of this preparation phase.

## Acceptance criteria

1. A versioned dataset contains 60 distinct semantic cases: 18 development and 42 sealed holdout, covering plan validity/order, step quality, cancellation, duplicates, transient/permanent failure, lease expiry, and crashes before/after provider response and effect commit.
2. Cases include expected plan/step behavior, prohibited effects, idempotency/recovery expectations, rubric, criticality, finite call/token/time caps, and 36 English / 24 Portuguese requests. At least three distinct cases cover every applicable family.
3. Campaign configuration includes three trials, maximum three normal provider calls per trial (plan plus at most two steps), cumulative request/token/spend limits, confirmation reserve, timeouts/retry/chunk/pacing/wall-clock limits and approval source. Expanded free-tier capacity and spend remain `PENDING`; paid ceiling remains zero.
4. Dry-run reports the 18-call pilot and 540-call full ceiling without SDK construction, credential reads, network or Docker mutation. Generation blocks before dispatch when any required cap, quota, approval or authenticated model preflight is missing.
5. Rubrics distinguish provider response from committed effect and never promise exactly-once provider billing. Offline regressions reject duplicate committed effects and unauthorized post-cancellation/auth-expiry effects. Service applicability and prerequisites are explicit.

## Out of scope

Provider execution, API/worker live runtime changes, Docker/service execution, effectful refunds, cloud deployment, sibling imports, public contracts, paid usage, or changing historic evidence.
