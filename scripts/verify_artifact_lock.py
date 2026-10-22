#!/usr/bin/env python3
"""Verify the committed local wheel against its provenance lock."""

import hashlib
import json
import pathlib
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
lock_path = ROOT / "artifacts/packages/artifact.lock.json"
lock = json.loads(lock_path.read_text(encoding="utf-8"))
wheel = ROOT / "artifacts/packages" / lock["artifact"]
wheel_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
source_lock=subprocess.check_output(["git","show",lock["source_commit"]+":"+lock["project_dependency_lock"]],cwd=ROOT)
dependency_hash = hashlib.sha256(source_lock).hexdigest()
if wheel_hash != lock["artifact_sha256"]:
    sys.exit("FAIL: wheel SHA-256 does not match artifact.lock.json")
if dependency_hash != lock["project_dependency_lock_sha256"]:
    sys.exit("FAIL: dependency lock SHA-256 does not match artifact.lock.json")
subprocess.run(["git", "merge-base", "--is-ancestor", lock["source_commit"], "HEAD"], cwd=ROOT, check=True)
with zipfile.ZipFile(wheel) as archive:
    metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
    metadata = set(archive.read(metadata_name).decode("utf-8").splitlines())
if f"Name: {lock['distribution']}" not in metadata or f"Version: {lock['version']}" not in metadata:
    sys.exit("FAIL: wheel metadata does not match artifact.lock.json")
fastapi_requirement = next((line.removeprefix("Requires-Dist: ") for line in metadata if line.startswith("Requires-Dist: fastapi")), None)
if fastapi_requirement != "fastapi<0.143.0,>=0.137.1":
    sys.exit(f"FAIL: wheel FastAPI requirement does not match supported range: {fastapi_requirement}")
print(f"artifact={wheel.name}")
print(f"artifact_sha256={wheel_hash}")
print(f"source_commit={lock['source_commit']}")
print(f"dependency_lock_sha256={dependency_hash}")
print(f"fastapi_requirement={fastapi_requirement}")
print("artifact-lock: PASS")
