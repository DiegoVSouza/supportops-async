# Verification plan

`uv export --locked --no-dev --no-emit-project --offline --format requirements-txt` exited0 and produced `locked-runtime-requirements.txt` with lockfile hashes. The `uv pip install --help` output confirms `--offline`, `--python-platform`, `--target`, `--only-binary` and `--require-hashes` are supported in the installed tool.

A provider-free local-cache probe using CPython3.13, `x86_64-manylinux_2_28`, binary-only, hashes and offline mode exited1. The first missing input is `psycopg-binary==3.2.10` for `cp313-manylinux2014_x86_64`; because resolution stopped there, other missing Linux wheels remain UNKNOWN. The exact URL is in `offline-cache-probe.json`; no artifact was downloaded, no image was built, and no gate ran. An offline-only Dockerfile proposal and hash-pinned runtime requirements are saved in phase-owned evidence, but the wheelhouse is incomplete and the proposal is not runtime-validated.

Next dependency: obtain a complete hash-matching Python3.13 Linux wheelhouse through an explicitly authorized, scoped acquisition if unavailable locally; then validate the complete finite build plan. A future full P04 gate requires separate explicit authorization; the phase033 exception remains consumed1/1 and must not be bypassed by a focused build. No operation032 invocation is eligible without its required passing gate and current binding.
