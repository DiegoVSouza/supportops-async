# Phase 017: Isolated service scenario recheck

## Objective

Revalidate the existing PostgreSQL and LocalStack SQS long-step, duplicate-delivery, retry, and dead-letter scenarios against the current P04 source without changing the candidate or touching shared service stacks.

## Scope and acceptance

- Run the existing `scripts/service_scenarios.py` against phase-owned PostgreSQL and LocalStack services using cached images and unique Compose project identity.
- Preserve candidate identity at source HEAD `0d427e3e9b509fec19450d52f45e35aab9bbed33`; this phase adds only SDD, evidence, and status/knowledge records.
- Record Docker resource identities/states before and after, exact commands, exit codes, sanitized output, and cleanup.
- Keep broader P04 acceptance INCOMPLETE: API/worker trace export, RAG, Terraform, model quality, independent review, and promotion are not established by these scenarios.

## Constraints

- No provider calls, credentials, paid usage, build, image pull, Terraform, deploy, or external effects.
- Start only the PostgreSQL and LocalStack services from `docker-compose.async.yml` under project `p04-phase017-isolated-service`, using their configured loopback ports 15432 and 14566 after verifying they are free.
- Never target or alter another Compose project, its containers, networks, or volumes. Clean up only this phase's Compose project.
- The scenario may create/delete uniquely named queues only inside its isolated LocalStack instance and writes test data only to the phase-owned database.
- User, independent, dataset/rubric, and promotion reviews remain PENDING.
