"""Start owned synthetic services and invoke the frozen operation at most once."""
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
sys.path.insert(0, str(PROJECT))
from scripts.docker_inventory_identity import compare, stable_rows

NAMESPACE = "p04-reviewed-live-039"
COMPOSE = ["docker", "compose", "-p", NAMESPACE, "-f", str(OUT / "live-compose.yml")]
COMMANDS = {
    "containers": ["docker", "ps", "-a", "--no-trunc", "--format", '{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.Label "com.docker.compose.project"}}'],
    "networks": ["docker", "network", "ls", "--no-trunc", "--format", '{{.ID}}|{{.Name}}|{{.Label "com.docker.compose.project"}}'],
    "volumes": ["docker", "volume", "ls", "--format", '{{.Name}}|{{.Label "com.docker.compose.project"}}'],
    "images": ["docker", "image", "ls", "--no-trunc", "--format", "{{.ID}}|{{.Repository}}:{{.Tag}}"],
}
records = []
env = {k: v for k, v in os.environ.items() if not k.startswith("GROQ_API_KEY")}
env.update(LLM_MODE="live", PYTHONUTF8="1", PYTHONPATH=str(PROJECT))

def run(command, timeout=60):
    try:
        result = subprocess.run(command, cwd=PROJECT, env=env, capture_output=True, text=True, timeout=timeout)
        record = {"command": command, "cwd": str(PROJECT), "exit_code": result.returncode, "output": result.stdout + result.stderr}
    except subprocess.TimeoutExpired:
        record = {"command": command, "cwd": str(PROJECT), "exit_code": 124, "output": "timeout; no replay"}
    records.append(record)
    (OUT / "live-commands.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record

def inventory():
    result = {}
    for name, command in COMMANDS.items():
        record = run(command)
        if record["exit_code"]: raise RuntimeError("inventory_unavailable")
        result[name] = sorted(record["output"].splitlines())
    return result

if (OUT / "invocation.json").exists() or (OUT / "live-result.json").exists():
    raise SystemExit("operation already invoked; no replay")
before = inventory()
if any(NAMESPACE in row for name in ("containers", "networks", "volumes") for row in before[name]):
    raise SystemExit("namespace already exists")
for port in (35532, 35566, 35580):
    with socket.socket() as probe: probe.bind(("127.0.0.1", port))
(OUT / "live-baseline.json").write_text(json.dumps({"inventory": before, "ports": [35532, 35566, 35580], "namespace": NAMESPACE}, indent=2) + "\n", encoding="utf-8", newline="\n")
if run(COMPOSE + ["config", "--quiet"])["exit_code"]: raise SystemExit("compose invalid")
up = run(COMPOSE + ["up", "-d", "--pull", "never", "--wait", "--wait-timeout", "150"], timeout=200)
dispatch = None
cleanup = None
try:
    if up["exit_code"] == 0:
        dispatch = run([sys.executable, "-m", "scripts.revalidation_operation"], timeout=240)
finally:
    current = inventory()
    preserved = all(stable_rows(before, k) <= stable_rows(current, k) for k in before)
    owned = [row for kind in ("containers", "networks", "volumes") for row in current[kind] if NAMESPACE in row]
    labels = all(row.endswith("|" + NAMESPACE) for row in owned)
    if owned and preserved and labels:
        cleanup = run(COMPOSE + ["down", "--volumes", "--remove-orphans"], timeout=120)["exit_code"]
    after = inventory()
    diff = compare(before, after)
    report = {"up_exit_code": up["exit_code"], "dispatch_exit_code": None if dispatch is None else dispatch["exit_code"],
              "cleanup_exit_code": cleanup, "owned_labels_verified": labels,
              "namespace_empty": not any(NAMESPACE in row for kind in ("containers", "networks", "volumes") for row in after[kind]),
              "baseline_diff": diff, "replay_allowed": False}
    (OUT / "live-orchestration-result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report))
