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
dependency_hash = hashlib.sha256((ROOT / lock["project_dependency_lock"]).read_bytes()).hexdigest()
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
print(f"artifact={wheel.name}")
print(f"artifact_sha256={wheel_hash}")
print(f"source_commit={lock['source_commit']}")
print(f"dependency_lock_sha256={dependency_hash}")
print("artifact-lock: PASS")
