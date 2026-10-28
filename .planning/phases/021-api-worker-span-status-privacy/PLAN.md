# Phase 021 plan

## Execution controls

- `llm_mode`: `fake`; no provider, credentials, network, Docker or external service.
- `allowed_write_paths`:
  - `.planning/phases/021-api-worker-span-status-privacy/**`
  - `supportops_async/api/app.py`
  - `supportops_async/worker/runner.py`
  - `tests/api/test_tasks_api.py`
  - `tests/worker/test_worker.py`
  - `tests/test_span_status_privacy.py`
  - `docs/harness/progress.md`
  - `docs/harness/failures.md`
  - `docs/harness/feature_list.json`
  - `docs/architecture.md`
  - `docs/knowledge/P04-async.md`
  - `artifacts/evidence/api-worker-span-privacy-021/**`
- `forbidden_changes`: exporter/collector configuration, trace schema/context propagation, API contracts, queue/store/effect semantics, locked dependencies, dataset/rubric/campaign/ledger/live evidence, prior phases, Docker/Compose/Terraform, sibling/root source, provider/credentials/external network, paid spend, deployment/push and weakened tests.
- Budget: USD 0; in-memory fake SDK only.
- Stop if the fix requires exporting actual exception content, changing error/retry semantics, dependency updates, historical evidence mutation or service lifecycle.

## Tasks

1. Add failing sync API-middleware and worker-process span tests using a unique synthetic sentinel and in-memory `TracerProvider` exporter; record the red result.
2. Pass `set_status_on_exception=False` to the API and worker outer spans; retain existing manual fixed error category and generic ERROR status. Prove exception propagation remains unchanged.
3. Run focused, fast and full fake gates; update scoped docs/evidence, inspect protected artifacts and staged diff, scan for secrets, commit implementation/evidence.

## Validation commands

- `uv run --locked --offline pytest -q --basetemp artifacts/evidence/api-worker-span-privacy-021/pytest tests/api/test_tasks_api.py tests/worker/test_worker.py`
- `uv run --locked --offline python scripts/check_fast.py`
- `P04_CHECK_EVIDENCE_DIR=artifacts/evidence/api-worker-span-privacy-021/full P04_PYTEST_BASETEMP=artifacts/evidence/api-worker-span-privacy-021/full-pytest PYTHONPATH=. uv run --locked --offline python scripts/check_full.py` (service dependencies may return project-accurate INCOMPLETE; do not start services).
- `git -c core.whitespace=cr-at-eol diff --cached --check`, staged path review and credential-pattern scan.

## Plan check

Three tasks, concrete project paths, zero-cost fake mode, no service/provider effects and explicit scope limits are defined. The project clean-context reviewer is not configured; this implementer phase does not claim independent review.
