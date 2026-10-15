#!/usr/bin/env python3
"""Fast structural and syntax checks for the P04 package."""

import json
import pathlib
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]

required = ["harness.yaml", "AGENTS.md", ".harness/modules.lock", "pyproject.toml", "uv.lock", "supportops_async/api/app.py", "supportops_async/store/sqlite.py", "supportops_async/worker/runner.py", "artifacts/packages/artifact.lock.json"]
missing = [name for name in required if not (ROOT / name).is_file()]
if missing:
    print(f"FAIL missing files: {missing}")
    sys.exit(1)

with (ROOT / "pyproject.toml").open("rb") as stream:
    project = tomllib.load(stream)
assert project["project"]["name"] == "supportops-async"
with (ROOT / "docs/harness/sources.lock.json").open(encoding="utf-8") as stream:
    json.load(stream)

compiled = subprocess.run([sys.executable, "-m", "compileall", "-q", "supportops_async", "scripts"], cwd=ROOT)
print(f"python -m compileall -q supportops_async scripts: exit={compiled.returncode}")
locked = subprocess.run(["uv", "lock", "--check"], cwd=ROOT)
print(f"uv lock --check: exit={locked.returncode}")
artifact = subprocess.run([sys.executable, "scripts/verify_artifact_lock.py"], cwd=ROOT)
print(f"python scripts/verify_artifact_lock.py: exit={artifact.returncode}")
print("check-fast: PASS" if compiled.returncode == locked.returncode == artifact.returncode == 0 else "check-fast: FAIL")
sys.exit(0 if compiled.returncode == locked.returncode == artifact.returncode == 0 else 1)
