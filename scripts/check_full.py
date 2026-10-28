#!/usr/bin/env python3
"""Run available P04 product checks and report unavailable integration gates."""

import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
INCOMPLETE = []
FAILED = []
IMAGE_TAG = os.getenv("P04_CHECK_IMAGE_TAG", "supportops-async:local-check")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*:[A-Za-z0-9][A-Za-z0-9_.-]*", IMAGE_TAG):
    print("check-full: FAIL invalid image tag")
    sys.exit(1)


def prepare_pytest_basetemp() -> pathlib.Path:
    configured = os.getenv("P04_PYTEST_BASETEMP", "artifacts/evidence/.pytest-tmp")
    evidence_root = (ROOT / "artifacts" / "evidence").resolve()
    candidate = (ROOT / configured).resolve()
    if not candidate.is_relative_to(evidence_root):
        raise ValueError("pytest base directory must be inside artifacts/evidence")
    if candidate.is_symlink() or candidate.exists():
        raise FileExistsError(f"pytest base directory already exists; refusing to clear it: {candidate}")
    candidate.mkdir(parents=True)
    return candidate


try:
    PYTEST_BASETEMP = prepare_pytest_basetemp()
except (OSError, ValueError) as error:
    print(f"check-full: FAIL unsafe pytest base directory: {error}")
    sys.exit(1)


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
pytest_basetemp_arg = str(PYTEST_BASETEMP.relative_to(ROOT))
print(f"pytest base directory: {pytest_basetemp_arg}")
run("unit-and-subprocess-tests", ["uv", "run", "--locked", "pytest", "-q", "-rs", "--basetemp", pytest_basetemp_arg, "tests"])
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
    run("docker-image-build", ["docker", "build", "--file", "Dockerfile", "--tag", IMAGE_TAG, "."])
else:
    INCOMPLETE.append("Docker image build: Docker daemon unavailable")

terraform = shutil.which("terraform")
localstack_endpoint = os.getenv("P04_LOCALSTACK_ENDPOINT")
terraform_dir = ROOT / "infra" / "terraform"
if terraform:
    terraform_prefix = [terraform, "-chdir=infra/terraform"]
elif docker_info.returncode == 0:
    terraform_image = "hashicorp/terraform:1.16.6"
    workspace = os.getenv("P04_TERRAFORM_WORKSPACE")
    mirror = os.getenv("P04_TERRAFORM_MIRROR")
    cli_config = os.getenv("P04_TERRAFORM_CLI_CONFIG")
    network = os.getenv("P04_TERRAFORM_NETWORK")
    endpoint = os.getenv("P04_TERRAFORM_ENDPOINT")
    if not all((workspace, mirror, cli_config, network, endpoint)):
        print("check-full: INCOMPLETE explicit Terraform workspace/mirror/config/network/endpoint required")
        sys.exit(2)
    if not re.fullmatch(r"p04-[a-z0-9-]+", network) or endpoint != "http://localstack:4566":
        print("check-full: FAIL unsafe Terraform network or endpoint")
        sys.exit(1)
    workspace_path = (ROOT / workspace).resolve()
    if not workspace_path.is_relative_to((ROOT / "artifacts/evidence").resolve()):
        print("check-full: FAIL Terraform workspace must be phase-owned evidence")
        sys.exit(1)
    terraform_mount = f"{workspace_path}:/workspace"
    localstack_endpoint = endpoint
    terraform_prefix = [
        "docker", "run", "--rm", "--pull=never", "--network", network,
        "-e", "TF_CLI_CONFIG_FILE=/terraform.rc",
        "-v", f"{pathlib.Path(mirror).resolve()}:/mirror:ro",
        "-v", f"{pathlib.Path(cli_config).resolve()}:/terraform.rc:ro",
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
        terraform_prefix + ["init", "-backend=false", "-input=false", "-lockfile=readonly"],
    )
    if init_rc == 0:
        run("terraform-validate", terraform_prefix + ["validate"])
        if localstack_endpoint:
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
