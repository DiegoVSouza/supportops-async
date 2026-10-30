"""Prepare and inventory an isolated offline P04 gate; does not run it."""
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tarfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
LAB = PROJECT.parents[1]
WORK = OUT / ".git" / "snapshot" / "lab" / "projects" / "p04"
ARCHIVE = OUT / "source.tar"
NAMESPACE = "p04-reentrant-validation-042"
IMAGE = "supportops-async:reentrant042"
PORTS = (40532, 40566, 40579, 40586, 40518, 40580)
IMAGES = ("postgres:17.11-alpine3.24", "localstack/localstack:4.14.0",
          "redis@sha256:becdda6c7f4b3fb42e42fd7f120bbf5c54c4caaaf16f26da24e4563d2c1f0576",
          "hashicorp/terraform:1.16.6", "jaegertracing/jaeger:2.18.0",
          "python:3.13.12-slim", "ghcr.io/astral-sh/uv:0.12.7")
OVERLAY = ("scripts/docker_inventory_identity.py", "tests/test_docker_inventory_identity.py",
           "scripts/credential_presence.py", "tests/test_credential_presence.py")
ROOT_OVERLAY = ("scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py",
                "scripts/harness/migrate_p01_p04_revalidation.py", "shared/policies/groq-free-campaign.json",
                ".planning/llm-live-readiness/phases/039-p01-p04-reviewed-revalidation/AUTHORIZATION.json",
                ".planning/llm-live-readiness/phases/047-p04-reentrant-operation/AUTHORIZATION.json")
env = {k: v for k, v in os.environ.items() if not k.startswith("GROQ_API_KEY")}
env.update(LLM_MODE="fake", UV_OFFLINE="1", PYTHONUTF8="1")
records = []


def run(cmd, cwd=PROJECT):
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    records.append({"command": cmd, "cwd": str(cwd), "exit_code": result.returncode,
                    "output": result.stdout + result.stderr})
    if result.returncode:
        raise RuntimeError("preparation command failed")
    return result.stdout


def save(status, reason=None):
    (OUT / "gate-preparation.json").write_text(json.dumps({
        "status": status, "reason": reason, "records": records,
        "gate_executed": False, "provider_accessed": False,
    }, indent=2) + "\n", encoding="utf-8", newline="\n")


try:
    if WORK.exists() or ARCHIVE.exists() or (OUT / "additional-gate-attempt.json").exists():
        raise RuntimeError("snapshot or attempt already exists")
    commands = {
        "containers": ["docker", "ps", "-a", "--no-trunc", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.Label \"com.docker.compose.project\"}}"],
        "networks": ["docker", "network", "ls", "--no-trunc", "--format", "{{.ID}}|{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
        "volumes": ["docker", "volume", "ls", "--format", "{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
        "images": ["docker", "image", "ls", "--no-trunc", "--format", "{{.ID}}|{{.Repository}}:{{.Tag}}"],
    }
    baseline = {name: sorted(run(cmd).splitlines()) for name, cmd in commands.items()}
    if any(NAMESPACE in row for kind in ("containers", "networks", "volumes") for row in baseline[kind]):
        raise RuntimeError("namespace already exists")
    if any(row.endswith("|" + IMAGE) for row in baseline["images"]):
        raise RuntimeError("image tag already exists")
    for port in PORTS:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    records.append({"command": "bind loopback ports", "cwd": str(PROJECT), "exit_code": 0,
                    "output": list(PORTS)})
    for image in IMAGES:
        run(["docker", "image", "inspect", image, "--format", "{{.Id}}"])
    run(["docker", "compose", "-p", NAMESPACE, "-f", str(OUT / "compose.yml"), "config", "--quiet"])
    run(["git", "archive", "HEAD", "--format=tar", "--output", str(ARCHIVE)])
    WORK.mkdir(parents=True)
    with tarfile.open(ARCHIVE) as source:
        source.extractall(WORK, filter="data")
    wheel_root = LAB / "artifacts/evidence/llm-live-readiness/additional-validation-043"
    coverage = json.loads((wheel_root / "wheelhouse-coverage.json").read_text(encoding="utf-8"))
    if coverage.get("exit_code") != 0 or coverage.get("network") is not False:
        raise RuntimeError("offline wheelhouse coverage incomplete")
    manifest = json.loads((wheel_root / "wheelhouse-manifest.json").read_text(encoding="utf-8"))
    for name, details in manifest["files"].items():
        source = wheel_root / "wheelhouse" / name
        if hashlib.sha256(source.read_bytes()).hexdigest() != details["sha256"]:
            raise RuntimeError("wheelhouse hash mismatch")
        target = WORK / "wheelhouse" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(PROJECT / "artifacts/evidence/offline-build-preparation-034/locked-runtime-requirements.txt",
                    WORK / "locked-runtime-requirements.txt")
    shutil.copyfile(PROJECT / "artifacts/evidence/offline-build-preparation-034/Dockerfile.offline-proposal",
                    WORK / "Dockerfile")
    records.append({"command": "verify and copy hash-pinned wheelhouse and offline Dockerfile",
                    "cwd": str(PROJECT), "exit_code": 0, "output": f'{len(manifest["files"])} wheels'})
    gate_script = WORK / "scripts/check_full.py"
    source_text = gate_script.read_text(encoding="utf-8")
    old = '["docker", "build", "--file", "Dockerfile", "--tag", IMAGE_TAG, "."]'
    new = '["docker", "build", "--network=none", "--file", "Dockerfile", "--tag", IMAGE_TAG, "."]'
    if source_text.count(old) != 1:
        raise RuntimeError("offline docker build wrapper mismatch")
    gate_script.write_text(source_text.replace(old, new), encoding="utf-8", newline="\n")
    records.append({"command": "configure snapshot docker build --network=none", "cwd": str(WORK),
                    "exit_code": 0, "output": "one build command constrained"})
    for base, target_base, paths in ((PROJECT, WORK, OVERLAY), (LAB, WORK.parents[1], ROOT_OVERLAY)):
        for name in paths:
            target = target_base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(base / name, target)
    for name in ("artifacts/evals/live/ledger.sqlite", "artifacts/evals/live/provider-usage.sqlite"):
        source, target = PROJECT / name, WORK / name
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as src:
                with sqlite3.connect(target) as dst:
                    src.backup(dst)
    terraform = WORK / "artifacts/evidence/reentrant-reviewed-operation-042/terraform-work"
    terraform.mkdir(parents=True)
    for source in (PROJECT / "infra/terraform").iterdir():
        if source.suffix == ".tf" or source.name == ".terraform.lock.hcl":
            shutil.copyfile(source, terraform / source.name)
    (OUT / "terraform.rc").write_text('provider_installation {\n filesystem_mirror {\n path = "/mirror"\n include = ["registry.terraform.io/hashicorp/aws"]\n }\n}\n', encoding="utf-8", newline="\n")
    protected = PROJECT / "artifacts/evidence/check-full.txt"
    (OUT / "baseline.json").write_text(json.dumps({"inventory": baseline,
        "namespace": NAMESPACE, "image": IMAGE, "ports": PORTS,
        "protected_sha256": hashlib.sha256(protected.read_bytes()).hexdigest()}, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    save("PASS")
    print("snapshot prepared, gate not executed")
except Exception as error:
    save("INCOMPLETE", str(error))
    print("preparation incomplete:", type(error).__name__)
    raise SystemExit(2)
