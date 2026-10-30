# Verification plan

PASS offline: the nested campaign lease was reproduced as `account_lease_busy`; the controller now performs applied audit, policy, registry and prefix checks under the already-held campaign lease and a separately acquired account lease. Targeted tests17 PASS, `check_fast` PASS, both exit0; evidence `artifacts/evidence/reentrant-migration-check-040/tests.json`. The previous live operation remains consumed and cannot be replayed. Current source has not passed a new full gate and the existing manifest is stale.
