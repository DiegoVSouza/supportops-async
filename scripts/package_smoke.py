"""Exercise the installed wheel without importing the source checkout."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.resources
import pathlib
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel-site", type=pathlib.Path, required=True)
    parser.add_argument("--dependency-site", type=pathlib.Path, required=True)
    parser.add_argument("--expected-version", default="0.1.2")
    args = parser.parse_args()
    sys.path.insert(0, str(args.wheel_site.resolve()))
    sys.path.insert(1, str(args.dependency_site.resolve()))

    from supportops_async.api.app import create_app
    from supportops_async.queue.contracts import BrokerMessage
    from supportops_async.queue.memory import InMemoryBroker
    from supportops_async.store.sqlite import SQLiteTaskStore
    from supportops_async.worker import Worker

    package_file = pathlib.Path(__import__("supportops_async").__file__).resolve()
    if args.wheel_site.resolve() not in package_file.parents:
        raise AssertionError(f"package imported outside installed wheel: {package_file}")
    if importlib.metadata.version("supportops-async") != args.expected_version:
        raise AssertionError("unexpected installed package version")
    requirements = importlib.metadata.distribution("supportops-async").requires or []
    if not any(requirement.lower().startswith("fastapi<0.143.0,>=0.137.1") for requirement in requirements):
        raise AssertionError(f"unexpected FastAPI compatibility requirement: {requirements}")
    import fastapi
    if fastapi.__version__ != "0.142.4":
        raise AssertionError(f"unexpected FastAPI consumer version: {fastapi.__version__}")
    migration = importlib.resources.files("supportops_async.store").joinpath("migrations/001_tasks.sql")
    if not migration.is_file():
        raise AssertionError("PostgreSQL migration was not included in the wheel")

    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, created = store.create({"steps": ["triage", "resolve"]}, "wheel-smoke")
    if not created:
        raise AssertionError("fresh idempotency key was not created")
    broker.publish(BrokerMessage(task.task_id))
    if not Worker(store, broker).run_once() or store.get(task.task_id).status.value != "done":
        raise AssertionError("installed wheel did not complete the local task")
    app = create_app(store, broker)
    if not any(route.path == "/tasks" for route in app.routes):
        raise AssertionError("installed API does not expose the task route")

    print(f"distribution_version={importlib.metadata.version('supportops-async')}")
    print(f"fastapi_version={fastapi.__version__}")
    print(f"package_file={package_file}")
    print(f"migration_in_wheel={migration}")
    print(f"task_status={store.get(task.task_id).status.value}")
    print("api_route=/tasks")
    print("package-smoke: PASS")


if __name__ == "__main__":
    main()
