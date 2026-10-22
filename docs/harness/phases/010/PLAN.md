# PLAN — Preserve work during early SQS redelivery

allowed_write_paths: supportops_async/worker/runner.py; supportops_async/__init__.py; pyproject.toml; uv.lock; tests/**; artifacts/**; docs/**; scripts/verify_artifact_lock.py; scripts/package_smoke.py

forbidden_changes: public contract break, sibling imports, unrelated stacks/files, root roadmap, kit, publish/push, apply, live LLM.

llm_mode: fake

dependencies: existing isolated PostgreSQL and LocalStack; pinned P04 tools.

1. Add the early-redelivery regression and save its failing output.
2. Defer failed claims, update the real crash test, release patch 0.1.3 and verify full gates.
3. Commit source, build wheel from that commit, record SHA/provenance and isolated consumer checks, then update state.

Checks: meaningful unit red/green, full unit/service gate, actual lease expiry and broker redelivery, package install/consumer, fast gate, staged diff and secret review.

Stop condition: missing services remain INCOMPLETE; no external exactly-once claim or package publication.

Plan review: accepted before product edits; internal correctness fix preserves API, release boundary and required recovery evidence are explicit.
