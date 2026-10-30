# Plan

1. Review the CPython3.13 Linux wheelhouse against the committed lock hashes and prepare a fresh snapshot with an offline wheelhouse build configuration and explicit baseline, ports, images and namespace.
2. Execute exactly one newly authorized complete fake gate after preflight, recording a persistent 1/1 marker immediately before the gate. Reconcile only proven-owned resources and preserve original Docker inventory identities.
3. Record gate and cleanup outcome, validate source/binding separately, and stop on failure or uncertainty. No P04 live dispatch follows automatically from the gate.

allowed_write_paths: `.planning/phases/036-wheelhouse-validation/**`, `artifacts/evidence/wheelhouse-validation-036/**`, `docs/harness/progress.md`. No source changes are authorized by this phase.

forbidden_changes: old reports/receipts/ledgers, policy, reserves, `gossett_backend`, other Docker resources, customer data, Terraform apply, paid use, fallback, provider/live calls, holdout or human evaluation. Fake mode, zero provider calls, paidUSD0. Additional gate max1; preserve historical3/3 and phase033 exception1/1. Stop on incomplete wheel coverage, changed baseline, unowned resource, missing marker persistence or gate failure. Plan-check is implementer self-assessment.
