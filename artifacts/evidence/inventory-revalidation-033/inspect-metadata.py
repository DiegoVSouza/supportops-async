"""Read Docker identity metadata and key presence without secret values."""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
LAB = PROJECT.parents[1]
records = []


def run(command):
    result = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True, timeout=30)
    records.append({"command": command, "cwd": str(PROJECT), "exit_code": result.returncode,
                    "output": result.stdout + result.stderr})
    return result


commands = [
    ["docker", "ps", "-a", "--no-trunc", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.Label \"com.docker.compose.project\"}}"],
    ["docker", "network", "ls", "--no-trunc", "--format", "{{.ID}}|{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
    ["docker", "volume", "ls", "--format", "{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
    ["docker", "image", "ls", "--no-trunc", "--format", "{{.ID}}|{{.Repository}}:{{.Tag}}"],
    ["docker", "inspect", "--format", "{{.Id}}|{{.Name}}|{{.Created}}|{{.Image}}|{{index .Config.Labels \"com.docker.compose.project\"}}|{{index .Config.Labels \"com.docker.compose.service\"}}", "gossett_backend"],
]
for command in commands:
    run(command)

historical = []
evidence = PROJECT / "artifacts/evidence"
for parent, directories, names in os.walk(evidence):
    directories[:] = [d for d in directories if not d.startswith(("snapshot", "full-snapshot", ".git", "pytest", "tmp"))]
    for name in names:
        if not name.startswith(("docker-inventory", "service-inventory", "docker-before", "docker-after")) or not name.endswith(".json"):
            continue
        path = Path(parent) / name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data.get("containers", [])
            if isinstance(rows, dict):
                rows = rows.get("output", "").splitlines()
            if not isinstance(rows, list):
                raise ValueError("unknown containers schema")
            historical.append({"path": path.relative_to(PROJECT).as_posix(),
                               "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                               "gossett_rows": [row for row in rows if isinstance(row, str) and "gossett_backend" in row],
                               "containers_format": "array" if isinstance(data.get("containers"), list) else "output"})
        except (OSError, ValueError, TypeError) as error:
            historical.append({"path": path.relative_to(PROJECT).as_posix(), "error_type": type(error).__name__})

names = ["GROQ_API_KEY", *(f"GROQ_API_KEY_{i}" for i in range(1, 5))]
file_presence = {name: False for name in names}
try:
    for line in (LAB / ".env").read_text(encoding="utf-8").splitlines():
        name, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and name.strip() in file_presence:
            file_presence[name.strip()] = bool(value.strip().strip('"').strip("'"))
    env_file_read = True
except OSError:
    env_file_read = False
presence = {name: {"process": bool(os.getenv(name)), "root_env": file_presence[name]} for name in names}
report = {"observed_utc": datetime.now(timezone.utc).isoformat(), "docker_commands": records,
          "historical_inventories": historical, "credential_presence": presence,
          "root_env_read": env_file_read, "credential_values_exposed": False,
          "provider_accessed": False, "docker_mutated": False,
          "historical_gap": "No ownership attribution or historical event completeness established by inventories."}
(OUT / "metadata-inventory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"docker_exits": [r["exit_code"] for r in records],
                  "inventories": len(historical), "credential_presence": presence,
                  "provider_accessed": False}))
raise SystemExit(0 if all(r["exit_code"] == 0 for r in records) else 2)
