# Plan

1. Implement the P04-owned accounted runner with durable per-step identities, bounded reservations, fixture-only session, sanitized permanent failures and strict triage/draft contracts.
2. Exercise API/worker integration, duplicate effects, cancellation and uncertain failure/restart with fake sessions; run locked focused/fast/full gates with new evidence/scratch paths. Preserve all previous outputs and report every service skip.

allowed_write_paths: .planning/phases/029-accounted-worker-boundary/**; supportops_async/accounted.py; tests/test_accounted_worker.py; artifacts/evidence/accounted-worker-029/**; docs/harness/progress.md.
forbidden_changes: old evidence/results/ledgers, direct provider guard removal, sibling imports, customer data, real effects, live credentials/calls, budgets/manifests, Docker lifecycle, Terraform apply, weakened tests and human approvals. Fake mode; zero provider calls and USD 0 paid. max_tries: 3 per failure. Stop on unknown work or accidental external access. Plan-check: implementer self-assessment. Full offline gates may be INCOMPLETE where services are deliberately unconfigured; do not claim full service acceptance.
