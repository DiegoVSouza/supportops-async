# Live campaign preparation — planning checks

No provider or Docker calls were made.

| Command | Exit | Observed result |
|---|---:|---|
| `uv run --locked python scripts/check_fast.py` | 0 | Artifact lock and local wheel provenance passed; Python compilation passed; `uv lock --check` passed; `check-fast: PASS`. |

The full check is deferred because it exercises Docker, external service dependencies, image build, and Terraform validation/plan. No service or cloud validation is claimed by this planning check.
