# Local wheel dependency and smoke gate

`artifacts/packages/artifact.lock.json` pins the P04 wheel SHA-256, source commit, Python range, direct dependency versions, and the hash of the full `uv.lock`. Install the wheel from the local artifact path; do not fetch P04 source from a sibling repository. The smoke run is offline and checks that imports resolve from the installed wheel.

Reproduce the tested offline wheel install and isolated smoke from the repository root:

```powershell
uv venv artifacts/packages/.venv --python 3.13.12
$env:UV_PROJECT_ENVIRONMENT = "artifacts/packages/.venv"
uv sync --project . --locked --offline --no-editable
Remove-Item Env:UV_PROJECT_ENVIRONMENT
uv pip install --offline --no-deps --python artifacts/packages/.venv/Scripts/python.exe artifacts/packages/supportops_async-0.1.2-py3-none-any.whl
artifacts/packages/.venv/Scripts/python.exe -I -S scripts/package_smoke.py --wheel-site artifacts/packages/.venv/Lib/site-packages --dependency-site artifacts/packages/.venv/Lib/site-packages
```

Set `UV_PROJECT_ENVIRONMENT=artifacts/packages/.venv` before the `uv sync` command to create the isolated dependency environment. The dependency graph comes from `uv.lock`; installing the wheel itself is offline and does not resolve or fetch dependencies.
