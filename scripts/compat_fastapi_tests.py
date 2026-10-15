"""Run P04 tests with an alternate FastAPI install and locked test dependencies."""

from __future__ import annotations

import argparse
import pathlib
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fastapi-site", type=pathlib.Path, required=True)
    parser.add_argument("--dependency-site", type=pathlib.Path, required=True)
    parser.add_argument("--expected-fastapi", default="0.142.4")
    parser.add_argument("--suite", choices=("api", "all"), default="all")
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(args.fastapi_site.resolve()), str(args.dependency_site.resolve()), str(root)]

    import pytest

    if args.suite == "api":
        test_args = ["-q", "--basetemp", "artifacts/evidence/.pytest-tmp/fastapi-1424-api", "tests/api"]
    else:
        test_args = [
            "-q",
            "-rs",
            "-m",
            "not integration",
            "--basetemp",
            "artifacts/evidence/.pytest-tmp/fastapi-1424-all",
            "tests",
        ]
    result = pytest.main(test_args)

    import fastapi

    print(f"FastAPI {fastapi.__version__}")
    if fastapi.__version__ != args.expected_fastapi:
        raise RuntimeError(f"wrong FastAPI version loaded: {fastapi.__version__}")
    raise SystemExit(result)


if __name__ == "__main__":
    main()
