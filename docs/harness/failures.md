# Failures

Record recurring builder or product failures here before fixing them.

## Implementation findings

- An initial unit run exposed an `UnboundLocalError` in outbox event creation caused by a function-local `uuid` import shadowing the module import. The local imports were removed and the full unit suite passes.
- pytest's default temporary directory could not be created reliably in the managed Windows environment. Checks now set `--basetemp artifacts/evidence/.pytest-tmp`; this directory is ignored.
- PostgreSQL, LocalStack, Docker daemon, and Terraform CLI are unavailable in this run. Their integration/build/plan gates remain INCOMPLETE rather than being represented by doubles.
- A clean full offline wheel install could not resolve `psycopg-binary==3.2.10` from the uv cache. The local wheel itself installed offline with `--no-deps`; the isolated smoke then used only the already installed, lock-pinned project dependency directory and confirmed wheel imports rather than checkout imports.
