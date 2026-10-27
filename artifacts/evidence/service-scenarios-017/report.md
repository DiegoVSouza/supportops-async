# Phase 017 — Isolated PostgreSQL/SQS service scenario recheck

Date: 2026-10-27

## Candidate and scope

The product-source candidate remained `0d427e3e9b509fec19450d52f45e35aab9bbed33` (the phase-016 implementation). Commits `3f5c686227f8abe15a2e5d44d6b2c96b5cf77af4` and `dbad3d1` contain phase planning only before this evidence commit; no runtime source, lock, dataset, rubric, prompt, or Compose file changed. Images were already present locally: PostgreSQL 17.11 `sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`; LocalStack 4.14.0 `sha256:3ebc37595918b8accb852f8048fef2aff047d465167edd655528065b07bc364a`.

No LLM provider was contacted. AWS test credentials were local placeholders for LocalStack only. No build, pull, Terraform, public listener, cloud action, or paid usage occurred.

## Results

- `uv run --locked python scripts/check_fast.py`: exit 0, PASS.
- `PYTHONPATH=. uv run --locked pytest -q -rs --basetemp artifacts/evidence/service-scenarios-017/pytest-tmp tests`: exit 0, 67 passed, 4 skipped because service env was not configured for this offline run.
- `docker compose -p p04-phase017-isolated-service -f docker-compose.async.yml config --quiet`: exit 0.
- `docker compose -p p04-phase017-isolated-service -f docker-compose.async.yml up --pull never --no-build -d --wait postgres localstack`: exit 0; only phase-owned PostgreSQL and LocalStack containers started.
- `uv run --locked python scripts/service_scenarios.py` with phase-local DSN/endpoint: exit 0. Long step PASS in 31.8 seconds, no competing claim, task done, one persisted effect. Duplicate delivery PASS, one claim and one effect record. Retry/DLQ PASS, failed after 3 attempts with exactly one DLQ message.
- `docker compose -p p04-phase017-isolated-service -f docker-compose.async.yml down --volumes --remove-orphans`: exit 0.

## Invocation correction

The plan initially named ports 16432/16566, but inspection of the checked-in Compose file showed fixed loopback mappings 15432/14566. The first command used the wrong endpoint, remained waiting without application database/SQS requests, and was interrupted. Its isolated resources were removed; the SDD ports were corrected, availability was checked, and the service run then passed. This was a local command configuration error, not an application semantic failure. A first direct pytest command also failed collection because `PYTHONPATH` was unset; the corrected project-root environment passed. Both failures are retained in their respective command/meta evidence.

## Docker reconciliation

Before and after cleanup: 102 pre-existing containers, 21 networks, and 89 volumes. Container identities, images, and normalized running/stopped/restarting states match; networks and volumes match. The phase namespace is empty. An unrelated `gossett_backend` container remained in its pre-existing `Restarting (1)` state; no command targeted it.

## Gate boundary

This phase verifies only offline controls and the PostgreSQL/SQS lease, duplicate-delivery, and retry/DLQ service scenarios. It does not demonstrate API/worker trace export, RAG behavior, image build, Terraform, model quality, customer behavior, or promotion. Those gates remain INCOMPLETE/PENDING. User, independent, dataset/rubric, and promotion reviews remain PENDING.

Detailed commands, output, exit codes, and inventories are adjacent in this directory. No response data or secrets are included.
