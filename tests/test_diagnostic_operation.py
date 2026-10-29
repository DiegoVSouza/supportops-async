import json
import pytest
from fastapi.testclient import TestClient
from scripts import diagnostic_operation as operation
from supportops_async.accounted import AccountedWorkflowRunner, STEPS
from supportops_async.worker.runner import PermanentFailure
from test_accounted_worker import setup_runtime, Session


def test_diagnostic_defaults_to_refusal_without_explicit_live(monkeypatch):
    monkeypatch.setenv("LLM_MODE","fake")
    with pytest.raises(operation.OperationBlocked,match="explicit_live"):
        operation.execute()


def test_full_diagnostic_reserve_is_single_use_and_keeps_original(tmp_path):
    from scripts.local_operation import reserve as original_reserve
    path=tmp_path/"ledger.sqlite"
    original=original_reserve(path)
    original.complete(case_id="fixture-local-01",trial=1,input_tokens=None,output_tokens=None,actual_cost_usd=None,outcome="incomplete",error_class="unknown")
    before=original.reserved_trials()
    diagnostic=operation.reserve(path)
    assert diagnostic.totals()["requests"]==6
    assert original.reserved_trials()==before
    with pytest.raises(operation.OperationBlocked,match="no_replay"):
        operation.reserve(path)


def test_scenario_is_trusted_and_distinct_not_payload_controlled(tmp_path):
    session=Session(tmp_path/"diagnostic.sqlite")
    runner=AccountedWorkflowRunner(session.path,session,scenario="greeting")
    runner({"operation_id":"fixture-diagnostic-01","steps":list(STEPS)},"triage")
    message=session.calls[0]["payload"]["messages"][-1]["content"]
    assert "greeting" in message and "tracking link" not in message
    with pytest.raises(PermanentFailure,match="synthetic_contract"):
        AccountedWorkflowRunner(session.path,session,scenario="customer")
    with pytest.raises(PermanentFailure,match="synthetic_contract"):
        runner({"operation_id":"fixture-diagnostic-02","steps":list(STEPS),"scenario":"tracking"},"triage")


def test_one_delivery_executes_both_steps_and_duplicate_reuses_task(tmp_path):
    from supportops_async.worker import Worker
    store,broker,session,_,client=setup_runtime(tmp_path)
    runner=AccountedWorkflowRunner(session.path,session,scenario="greeting")
    def submit():
        return client.post("/tasks",headers={"Idempotency-Key":"fixture-diagnostic-01"},json={"payload":{"operation_id":"fixture-diagnostic-01"},"steps":list(STEPS)})
    identifier=submit().json()["task_id"]
    worker=Worker(store,broker,runner=runner)
    assert worker.run_once()
    assert not worker.run_once()
    assert client.get("/tasks/"+identifier).json()["status"]=="done"
    assert submit().json()["task_id"]==identifier
    assert len(session.calls)==2
