"""Compare Docker inventory identities while ignoring changing status age."""
from __future__ import annotations

from typing import Any


def stable_rows(inventory: dict[str, Any], kind: str) -> set[tuple[str, ...]]:
    value = inventory[kind]
    if isinstance(value, dict):
        if value.get("exit_code") not in (None, 0):
            raise ValueError("inventory command failed")
        value = value.get("output", "").splitlines()
    if not isinstance(value, list):
        raise ValueError("unknown inventory format")
    result = set()
    for row in value:
        if not isinstance(row, str):
            raise ValueError("invalid inventory row")
        fields = row.split("|")
        if kind == "containers":
            if len(fields) != 6 or not fields[0] or not fields[1]:
                raise ValueError("invalid container identity")
            fields = fields[:3] + fields[4:]
        elif kind in {"networks", "volumes", "images"}:
            if not fields[0]:
                raise ValueError("invalid resource identity")
        else:
            raise ValueError("unknown inventory kind")
        identity = tuple(fields)
        if identity in result:
            raise ValueError("duplicate resource identity")
        result.add(identity)
    return result


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, list]]:
    result = {}
    for kind in ("containers", "networks", "volumes", "images"):
        old, new = stable_rows(before, kind), stable_rows(after, kind)
        result[kind] = {"missing": sorted(old - new), "added": sorted(new - old)}
    return result
