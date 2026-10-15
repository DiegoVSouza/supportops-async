# Local wheel dependency and smoke gate

`artifacts/packages/artifact.lock.json` pins the P04 wheel SHA-256, source commit, Python range, direct dependency versions, and the hash of the full `uv.lock`. Install the wheel from the local artifact path; do not fetch P04 source from a sibling repository. The smoke run is offline and checks that imports resolve from the installed wheel.

Reproduce the tested offline wheel install and isolated smoke from the repository root:

```powershell
uv venv artifacts/packages/.venv --python 3.13.12
uv pip install --offline --no-deps --python artifacts/packages/.venv/Scripts/python.exe artifacts/packages/supportops_async-0.1.0-py3-none-any.whl
artifacts/packages/.venv/Scripts/python.exe -I -S scripts/package_smoke.py --wheel-site artifacts/packages/.venv/Lib/site-packages --dependency-site .venv/Lib/site-packages
```

The dependency site is the already locked project environment. A self-contained offline resolver run needs a wheelhouse that contains `psycopg-binary==3.2.10`.
