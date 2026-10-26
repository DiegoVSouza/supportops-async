# Verify — Live campaign preparation

Use repository artifacts and commands, not implementation-chat claims. Save each command, exit code and sanitized output under `artifacts/evidence/live-campaign-preparation/`.

- [ ] Exactly 60 distinct semantic cases exist, 18 development and 42 sealed holdout, with all applicable families covered at least three times.
- [ ] User requests balance to 36 English and 24 Portuguese; related scenarios do not cross split boundaries.
- [ ] Cases encode expected plan/order/step behavior, side-effect restrictions, cancellation/expiry, duplicate handling, recovery outcome, rubric and finite caps.
- [ ] Graders distinguish provider response from durable effect commit and reject duplicate committed effects or unauthorized post-cancel/post-expiry effects.
- [ ] Campaign config contains three trials, maximum 3 calls per trial, all cumulative/per-task ceilings, confirmation reserve, timeout/retry/chunk/pacing/wall-clock settings and budget source.
- [ ] Dry-run shows 18-call pilot and 540-call full ceilings, exposes every USD 0 / `PENDING` blocker, and does not access SDK, secrets, network or Docker.
- [ ] Generation stops before provider dispatch while any required approval, quota, ceiling, service precondition or model preflight is missing.
- [ ] Safe fake checks pass with no unexpected skips. Docker/Terraform checks are not claimed unless executed and recorded in a later authorized phase.
- [ ] No demo-only run is described as API/worker service acceptance; no provider billing exactly-once claim is made.
- [ ] Staged changes are within allowed paths and contain no secrets or unrelated user data.
