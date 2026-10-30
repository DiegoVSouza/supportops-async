"""Run the one authorized additional P04 gate with owned-resource checks."""
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
WORK = OUT / ".git/snapshot/lab/projects/p04"
sys.path.insert(0, str(PROJECT))
from scripts.docker_inventory_identity import compare, stable_rows

NAMESPACE = "p04-reentrant-validation-042"
IMAGE = "supportops-async:reentrant042"
COMMANDS = {
    "containers": ["docker", "ps", "-a", "--no-trunc", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.Label \"com.docker.compose.project\"}}"],
    "networks": ["docker", "network", "ls", "--no-trunc", "--format", "{{.ID}}|{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
    "volumes": ["docker", "volume", "ls", "--format", "{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
    "images": ["docker", "image", "ls", "--no-trunc", "--format", "{{.ID}}|{{.Repository}}:{{.Tag}}"],
}
env = {k: v for k, v in os.environ.items() if not k.startswith("GROQ_API_KEY")}
env.update(LLM_MODE="fake", UV_OFFLINE="1", PYTHONPATH=str(WORK), PYTHONUTF8="1",
           PYTHONIOENCODING="utf-8", COMPOSE_PROJECT_NAME=NAMESPACE,
           P04_POSTGRES_DSN="postgresql://supportops:supportops@127.0.0.1:40532/supportops",
           P04_LOCALSTACK_ENDPOINT="http://127.0.0.1:40566",
           P04_TEST_REDIS_URL="redis://127.0.0.1:40579/0",
           P04_PYTEST_BASETEMP="artifacts/evidence/reentrant-reviewed-operation-042/pytest-tmp",
           P04_CHECK_IMAGE_TAG=IMAGE,
           P04_TERRAFORM_WORKSPACE="artifacts/evidence/reentrant-reviewed-operation-042/terraform-work",
           P04_TERRAFORM_MIRROR=str(PROJECT / "infra/terraform/.terraform/providers"),
           P04_TERRAFORM_CLI_CONFIG=str(OUT / "terraform.rc"),
           P04_TERRAFORM_NETWORK=NAMESPACE + "-local",
           P04_TERRAFORM_ENDPOINT="http://localstack:4566")
records = []


def run(command, cwd=PROJECT, timeout=60):
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                                encoding="utf-8", errors="replace", timeout=timeout)
        record = {"command": command, "cwd": str(cwd), "exit_code": result.returncode,
                  "output": result.stdout + result.stderr}
    except subprocess.TimeoutExpired as error:
        record = {"command": command, "cwd": str(cwd), "exit_code": 124,
                  "output": str(error.stdout or "") + str(error.stderr or "")}
    records.append(record)
    (OUT / "gate-commands.json").write_text(json.dumps(records, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
    return record


def inventory():
    values = {}
    for name, command in COMMANDS.items():
        record = run(command)
        if record["exit_code"]:
            raise RuntimeError("docker inventory unavailable")
        values[name] = sorted(record["output"].splitlines())
    return values


if (OUT / "additional-gate-attempt.json").exists():
    raise SystemExit("additional gate already consumed")
preparation = json.loads((OUT / "gate-preparation.json").read_text(encoding="utf-8"))
baseline_record = json.loads((OUT / "baseline.json").read_text(encoding="utf-8"))
if preparation["status"] != "PASS" or not WORK.is_dir():
    raise SystemExit("preparation is incomplete")
before = baseline_record["inventory"]
current = inventory()
diff = compare(before, current)
if any(v["missing"] or v["added"] for v in diff.values()):
    (OUT / "pre-gate-drift.json").write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8", newline="\n")
    raise SystemExit("baseline changed before service start")
for port in baseline_record["ports"]:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", port))
compose = ["docker", "compose", "-p", NAMESPACE, "-f", str(OUT / "compose.yml")]
gate_code = None
cleanup_code = None
up = run(compose + ["up", "-d", "--pull", "never", "--wait", "--wait-timeout", "150"], timeout=200)
try:
    if up["exit_code"] == 0:
        command = [sys.executable, "scripts/check_full.py"]
        with (OUT / "additional-gate-attempt.json").open("x", encoding="utf-8", newline="\n") as marker:
            json.dump({"historical_attempts": "3/3", "phase033_exception": "1/1", "phase036_exception": "1/1",
                       "state": "CONSUMED", "command": command, "cwd": str(WORK)}, marker)
            marker.flush()
            os.fsync(marker.fileno())
        gate_code = run(command, cwd=WORK, timeout=900)["exit_code"]
finally:
    current = inventory()
    baseline_preserved = all(stable_rows(before, k) <= stable_rows(current, k) for k in before)
    owned_rows = [(kind, row) for kind in ("containers", "networks", "volumes")
                  for row in current[kind] if NAMESPACE in row]
    labels_verified = all(row.endswith("|" + NAMESPACE) for _, row in owned_rows)
    if owned_rows and baseline_preserved and labels_verified:
        cleanup_code = run(compose + ["down", "--volumes", "--remove-orphans"], timeout=120)["exit_code"]
    after = inventory()
    image_rows = [row for row in after["images"] if row.endswith("|" + IMAGE)]
    if image_rows and gate_code is not None and baseline_preserved and labels_verified:
        image_remove = run(["docker", "image", "rm", IMAGE], timeout=60)["exit_code"]
        after = inventory()
    else:
        image_remove = 0 if not image_rows else 2
    final_diff = compare(before, after)
    protected = hashlib.sha256((PROJECT / "artifacts/evidence/check-full.txt").read_bytes()).hexdigest()
    namespace_empty = not any(NAMESPACE in row for k in ("containers", "networks", "volumes") for row in after[k])
    preserved = not any(v["missing"] or v["added"] for v in final_diff.values())
    passed = (gate_code == 0 and cleanup_code == 0 and image_remove == 0 and namespace_empty
              and preserved and protected == baseline_record["protected_sha256"])
    report = {"status": "PASS" if passed else "INCOMPLETE", "gate_exit_code": gate_code,
              "gate_consumed": gate_code is not None, "up_exit_code": up["exit_code"],
              "cleanup_exit_code": cleanup_code, "image_remove_exit_code": image_remove,
              "owned_labels_verified": labels_verified, "namespace_empty": namespace_empty,
              "protected_output_unchanged": protected == baseline_record["protected_sha256"],
              "baseline_diff": final_diff, "provider_accessed": False, "live_operation_invoked": False}
    (OUT / "gate-result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k != "baseline_diff"}, sort_keys=True))
raise SystemExit(0 if passed else 2)
