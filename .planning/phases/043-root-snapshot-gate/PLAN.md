# Plan

1. `prepare-gate.py`: Docker inventory, port/cache/namespace validation, snapshot of p04 HEAD plus the lab root state, read-only ledger copies, offline wheelhouse.
2. `run-gate.py`: start the owned namespace, consume the marker, run `check_full.py` once, clean only owned resources, reconcile the baseline.
3. Record the result in VERIFY.md and `docs/harness/progress.md`, then commit.

allowed_write_paths: `.planning/phases/043-root-snapshot-gate/**`, `artifacts/evidence/root-snapshot-gate-043/**`, `docs/harness/progress.md`.

forbidden_changes: product source, frozen manifests, source ledgers, root policy, root `.runtime/`, `.env`, credentials, provider or live invocation, Docker resources outside `p04-root-snapshot-043`, `terraform apply`, weakening any test or assertion.

llm_mode: fake. budget: USD 0, zero provider calls, one gate. validation: `python artifacts/evidence/root-snapshot-gate-043/run-gate.py`.

stop conditions: preparation not PASS, baseline drift before start, marker already present, or a failed gate (the `max_tries` counter for this failure family continues from phase042; a repair needs a cause-level source fix and is recorded here).
