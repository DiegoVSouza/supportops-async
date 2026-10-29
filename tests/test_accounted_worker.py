import json
import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from supportops_async.accounted import MODEL, STEPS, AccountedWorkflowRunner
from supportops_async.api.app import create_app
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker
from supportops_async.worker.runner import PermanentFailure


class Session:
    provenance = "fixture"

    def __init__(self, path):
        self.path, self.calls = path, []
        self.error = None

    def preview(self, envelope):
        with closing(sqlite3.connect(self.path)) as db:
            assert db.execute("SELECT COUNT(*) FROM attempts WHERE status='reserved'").fetchone()[0] == 1

    def complete(self, envelope):
        self.calls.append(envelope)
        if self.error:
            raise self.error
        field, value = ("category", "shipping") if envelope["call_index"] == 1 else ("response", "Check the synthetic tracking link.")
        return {"status": "ok", "model": MODEL, "attempt_id": str(len(self.calls)) * 32,
                "usage": {"input_tokens": 100, "output_tokens": 20}, "content": json.dumps({field: value})}


def setup_runtime(tmp_path):
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    session = Session(tmp_path / "accounted.sqlite")
    runner = AccountedWorkflowRunner(session.path, session)
    return store, broker, session, runner, TestClient(create_app(store, broker))


def submit(client, key="fixture-one"):
    return client.post("/tasks", headers={"Idempotency-Key": key},
                       json={"payload": {"operation_id": key}, "steps": list(STEPS)})


def test_real_api_worker_duplicate_delivery_has_two_accounted_calls(tmp_path):
    store, broker, session, runner, client = setup_runtime(tmp_path)
    response = submit(client)
    task = response.json()["task_id"]
    assert response.status_code == 202
    assert submit(client).json()["task_id"] == task
    worker = Worker(store, broker, runner=runner)
    assert worker.run_once() and worker.run_once()
    assert client.get("/tasks/" + task).json()["status"] == "done"
    assert len(session.calls) == 2
    assert store.effect(task, "1:triage")["category"] == "shipping"


def test_timeout_is_permanent_and_new_operation_cannot_bypass(tmp_path):
    store, broker, session, runner, client = setup_runtime(tmp_path)
    session.error = TimeoutError("PRIVATE")
    task = submit(client).json()["task_id"]
    worker = Worker(store, broker, runner=runner)
    worker.run_once()
    assert store.get(task).status.value == "failed"
    assert len(broker.dead_letters) == 1
    assert broker.nack_delays == []
    restarted = AccountedWorkflowRunner(session.path, Session(session.path))
    with pytest.raises(PermanentFailure, match="prior_work"):
        restarted({"operation_id": "fixture-new", "steps": list(STEPS)}, "triage")
    assert len(session.calls) == 1


def test_cancelled_api_task_never_dispatches(tmp_path):
    store, broker, session, runner, client = setup_runtime(tmp_path)
    task = submit(client).json()["task_id"]
    assert client.post("/tasks/" + task + "/cancel").status_code == 202
    Worker(store, broker, runner=runner).run_once()
    assert session.calls == []


def test_live_session_and_unknown_payload_are_denied(tmp_path):
    session = Session(tmp_path / "op.sqlite")
    session.provenance = "live"
    with pytest.raises(PermanentFailure, match="fixture_session"):
        AccountedWorkflowRunner(session.path, session)
    session.provenance = "fixture"
    runner = AccountedWorkflowRunner(session.path, session)
    with pytest.raises(PermanentFailure, match="synthetic_contract"):
        runner({"operation_id": "fixture-one", "steps": list(STEPS), "customer_data": "PRIVATE"}, "triage")
    assert not session.path.exists()
