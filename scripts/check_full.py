#!/usr/bin/env python3
"""Run available P04 product checks and report unavailable integration gates."""

import os
import pathlib
import shutil
import socket
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
INCOMPLETE = []
FAILED = []


def run(name: str, command: list[str], *, cwd: pathlib.Path = ROOT) -> int:
    print(f"\nCOMMAND: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(f"EXIT_CODE: {result.returncode}")
    print("OUTPUT:")
    print(result.stdout.rstrip() or "(empty)")
    if result.returncode:
        FAILED.append(name)
    return result.returncode


run("fast", [sys.executable, "scripts/check_fast.py"])
run("unit-and-subprocess-tests", ["uv", "run", "--locked", "pytest", "-q", "-rs", "--basetemp", "artifacts/evidence/.pytest-tmp", "tests"])
compose_rc = run("compose-config", ["docker", "compose", "-f", "docker-compose.async.yml", "config", "--quiet"])
if compose_rc == 0:
    print("STATUS compose-config: PASS")

try:
    with socket.create_connection(("127.0.0.1", 5432), timeout=0.5):
        pg_reachable = True
except OSError:
    pg_reachable = False
if not os.getenv("P04_POSTGRES_DSN") or not pg_reachable:
    INCOMPLETE.append("PostgreSQL integration: P04_POSTGRES_DSN and reachable local server required")
if not os.getenv("P04_LOCALSTACK_ENDPOINT"):
    INCOMPLETE.append("LocalStack integration: P04_LOCALSTACK_ENDPOINT required")

docker_info = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("\nCOMMAND: docker info --format {{.ServerVersion}}")
print(f"EXIT_CODE: {docker_info.returncode}\nOUTPUT:\n{docker_info.stdout.rstrip() or '(empty)'}")
if docker_info.returncode == 0:
    run("docker-image-build", ["docker", "build", "--file", "Dockerfile", "--tag", "supportops-async:local-check", "."])
else:
    INCOMPLETE.append("Docker image build: Docker daemon unavailable")

terraform = shutil.which("terraform")
if terraform:
    run("terraform-init", [terraform, "-chdir=infra/terraform", "init", "-backend=false"])
    run("terraform-validate", [terraform, "-chdir=infra/terraform", "validate"])
    if os.getenv("P04_LOCALSTACK_ENDPOINT"):
        run("terraform-plan", [terraform, "-chdir=infra/terraform", "plan", "-input=false"])
    else:
        INCOMPLETE.append("Terraform plan: local LocalStack endpoint unavailable")
else:
    INCOMPLETE.append("Terraform validate/plan/provider lock: Terraform CLI unavailable")

for item in INCOMPLETE:
    print(f"STATUS INCOMPLETE: {item}")
for item in FAILED:
    print(f"STATUS FAIL: {item}")
if FAILED:
    print("check-full: FAIL")
    sys.exit(1)
if INCOMPLETE:
    print("check-full: INCOMPLETE")
    sys.exit(2)
print("check-full: PASS")
