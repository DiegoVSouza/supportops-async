# Verify — Live campaign preparation

Use repository artifacts and commands, not implementation-chat claims. Save each command, exit code and sanitized output under `artifacts/evidence/live-campaign-preparation/`.

- [x] Validator and tests confirm 60 unique cases, 18 development / 42 fixed holdout, eight required families with at least seven scenarios each. Holdout access is not technically restricted; independent outcome review remains pending.
- [x] Language denominator is 36 English / 24 Portuguese; duplicate source groups and cross-split reuse are rejected.
- [x] Cases specify expected plan/step outcomes, cancellation, expiry, duplicate delivery, crash boundary, prohibited effects, recovery expectations, real service prerequisites, rubrics and finite caps.
- [x] Tests reject invalid plans/steps with committed effects, duplicate effects, post-cancel/post-auth-expiry effects, and confusion between provider response and effect commit. Exactly-once provider billing claims fail.
- [x] Config reports three trials, max 3 calls per trial, finite task/call/token/time caps, 180-call confirmation reserve, retry/chunk/pacing/wall-clock controls, USD 0 source. Unapproved cumulative caps remain PENDING.
- [x] `-S` dry-runs report pilot 18, development 162, holdout 378, primary 540 calls and additive 738 including confirmation, with USD 0 blockers and no provider/credential/network/Docker access.
- [x] Generation is disabled and exits `INCOMPLETE` before provider dispatch while budget/quota, reviews, service identity, caps and model preflight remain pending.
- [x] Ten focused preparation tests and `check_fast` pass. Unit suite passes 53 tests; four service-dependent tests skip because local PostgreSQL/LocalStack/Redis environment variables are not configured. Docker/Terraform full gate was deferred.
- [x] SQLite/in-memory demos are excluded from service evidence; no exactly-once provider billing or live service claim is made.
- [x] Staged paths are within phase ownership; reviewed diff has no credentials or unrelated user data.


## Outstanding phase gates

- Independent case/rubric reviewer: `PENDING`.
- Clean-context verification: `PENDING`; project profile does not provide a clean-context reviewer.
- Service identity, ports, dependency health, and real PostgreSQL/LocalStack/Redis acceptance: `PENDING` for a separately authorized phase.
- Paid budget remains USD 0. Free-tier quota, cumulative request/token ceilings, confirmation funding, pacing, wall-clock cap, authenticated model catalog, durable campaign ledger and lease are unresolved; campaign generation stays disabled.
