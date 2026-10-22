#!/usr/bin/env python3
"""Run available P04 product checks and report unavailable integration gates."""

import os
import pathlib
import shutil
import socket
import subprocess
import sys
from urllib.parse import urlsplit

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

pg_dsn = os.getenv("P04_POSTGRES_DSN")
pg_reachable = False
pg_target = "not configured"
if pg_dsn:
    parsed_dsn = urlsplit(pg_dsn)
    if parsed_dsn.scheme in {"postgres", "postgresql"} and parsed_dsn.hostname:
        pg_host = parsed_dsn.hostname
        pg_port = parsed_dsn.port or 5432
        pg_target = f"{pg_host}:{pg_port}"
        try:
            with socket.create_connection((pg_host, pg_port), timeout=0.5):
                pg_reachable = True
        except OSError:
            pass
print(f"PostgreSQL TCP probe: {pg_target}; reachable={pg_reachable}")
if not pg_dsn or not pg_reachable:
    INCOMPLETE.append("PostgreSQL integration: P04_POSTGRES_DSN and reachable local server required")
if not os.getenv("P04_LOCALSTACK_ENDPOINT"):
    INCOMPLETE.append("LocalStack integration: P04_LOCALSTACK_ENDPOINT required")
if pg_reachable and os.getenv("P04_LOCALSTACK_ENDPOINT"):
    run("long-step-retry-dlq-services", [sys.executable, "scripts/service_scenarios.py"])

docker_info = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("\nCOMMAND: docker info --format {{.ServerVersion}}")
print(f"EXIT_CODE: {docker_info.returncode}\nOUTPUT:\n{docker_info.stdout.rstrip() or '(empty)'}")
if docker_info.returncode == 0:
    run("docker-image-build", ["docker", "build", "--file", "Dockerfile", "--tag", "supportops-async:local-check", "."])
else:
    INCOMPLETE.append("Docker image build: Docker daemon unavailable")

terraform = shutil.which("terraform")
localstack_endpoint = os.getenv("P04_LOCALSTACK_ENDPOINT")
terraform_dir = ROOT / "infra" / "terraform"
if terraform:
    terraform_prefix = [terraform, "-chdir=infra/terraform"]
elif docker_info.returncode == 0:
    terraform_image = "hashicorp/terraform:1.16.6"
    terraform_mount = f"{terraform_dir.resolve()}:/workspace"
    terraform_prefix = [
        "docker", "run", "--rm",
        "-e", "AWS_ACCESS_KEY_ID=test",
        "-e", "AWS_SECRET_ACCESS_KEY=test",
        "-e", "AWS_DEFAULT_REGION=us-east-1",
        "-v", terraform_mount,
        "-w", "/workspace",
        terraform_image,
    ]
else:
    terraform_prefix = []

if terraform_prefix:
    init_rc = run(
        "terraform-init",
        terraform_prefix + ["init", "-backend=false", "-input=false"],
    )
    if init_rc == 0:
        run("terraform-validate", terraform_prefix + ["validate"])
        if localstack_endpoint:
            if not terraform:
                parsed_endpoint = urlsplit(localstack_endpoint)
                if parsed_endpoint.hostname in {"localhost", "127.0.0.1"}:
                    endpoint_host = f"host.docker.internal:{parsed_endpoint.port or 4566}"
                    localstack_endpoint = parsed_endpoint._replace(
                        netloc=endpoint_host
                    ).geturl()
            run(
                "terraform-plan",
                terraform_prefix
                + ["plan", "-input=false", f"-var=localstack_endpoint={localstack_endpoint}"],
            )
        else:
            INCOMPLETE.append("Terraform plan: local LocalStack endpoint unavailable")
else:
    INCOMPLETE.append("Terraform validate/plan/provider lock: Terraform CLI and Docker unavailable")

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
