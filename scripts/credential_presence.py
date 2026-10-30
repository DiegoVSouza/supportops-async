"""Report credential presence in process and root .env without exposing values."""
from pathlib import Path
from collections.abc import Mapping

NAMES = ("GROQ_API_KEY", *(f"GROQ_API_KEY_{i}" for i in range(1, 5)))


def presence(root: Path, environment: Mapping[str, str]) -> dict[str, dict[str, bool]]:
    file_values = {name: False for name in NAMES}
    try:
        lines = (root / ".env").read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []
    for line in lines:
        name, separator, value = line.strip().removeprefix("export ").partition("=")
        name = name.strip()
        if separator and name in file_values:
            file_values[name] = bool(value.strip().strip('"').strip("'"))
    return {name: {"process": bool(environment.get(name)), "root_env": file_values[name]}
            for name in NAMES}
