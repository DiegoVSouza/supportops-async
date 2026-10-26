# P04 Phase 011 — campaign preparation evidence

All new preparation and grader evidence is offline and synthetic. No Groq call, catalog lookup, credential read, network access, Docker mutation, real refund, external effect, or service acceptance claim was made. Paid authorization remains USD 0.

| Command | Exit | Result |
|---|---:|---|
| `uv run --locked python scripts/run_live_campaign.py --stage pilot --dry-run` | 0 | 6 cases × 1 trial × 3 calls = 18 calls. |
| `uv run --locked python scripts/run_live_campaign.py --stage development --dry-run` | 0 | 18 cases × 3 trials × 3 calls = 162 calls. |
| `uv run --locked python scripts/run_live_campaign.py --stage holdout --dry-run` | 0 | 42 cases × 3 trials × 3 calls = 378 calls. |
| `uv run --locked python -m unittest discover -s tests -p test_live_campaign_preparation.py -v` | 0 | 10 focused contract tests passed. |
| `uv run --locked python scripts/check_fast.py` | 0 | `check-fast: OK`. |
| `uv run --locked python -m pytest tests --basetemp <phase-local-temp> -q -rs` | 0 | 53 passed, 4 service-dependent tests skipped because PostgreSQL/LocalStack/Redis settings were not configured. Temp tree was removed after the run. |

A default-temp pytest attempt first failed because pytest could not scan the user-profile temp directory (Windows access denied); its output is preserved in `unit-suite.txt`. The project-local temporary base resolved the environment issue; full successful output and skip reasons are in `unit-suite-isolated-temp.txt` and `unit-suite-skips.txt`.

Dataset SHA-256: `64e835a0ce1e9faa7b4435b4362e0a821bb70b6850adb4a74ba3d2edabe433c6`. It has 60 synthetic cases, 18 development / 42 holdout, 36 English / 24 Portuguese, and eight families (7–8 cases each). Each trial is capped at three calls, 12,288 input and 1,536 output tokens, 120 seconds per task, and 30 seconds per provider call.

Planned maxima, not authorization or consumption: primary 540 calls / 2,211,840 input / 276,480 output tokens; fresh confirmation 20 cases × 3 trials × 3 calls = 180 calls / 737,280 input / 92,160 output tokens; pilot + primary + confirmation additive 738 calls / 3,022,848 input / 377,856 output tokens. Paid budget remains USD 0. Quota, cumulative caps, funding, review, service identity/ports, model preflight, pacing, wall-clock cap, durable ledger/lease, and clean-context review remain pending.

Detailed dry-run reports and command outputs are stored beside this report. The unit skips and lack of service prerequisites leave live service readiness `INCOMPLETE`.
