from supportops_async.queue.memory import InMemoryBroker
from supportops_async.queue.contracts import BrokerMessage
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker
from supportops_async.worker.runner import FakeRunner, PermanentFailure, TransientFailure


def test_duplicate_delivery_completes_once_and_acks_both():
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["triage", "refund"], "operation_id": "op1"}, "dup")
    broker.publish(BrokerMessage(task.task_id))
    broker.publish(BrokerMessage(task.task_id))
    worker = Worker(store, broker)
    assert worker.run_once() and worker.run_once()
    assert store.get(task.task_id).status.value == "done"
    assert store.effect(task.task_id, "2:refund")["effect_key"] == "op1:2:refund"
    assert not broker.dead_letters


def test_transient_failure_retries_with_cap_then_dlq():
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["triage"], "fail_step": "triage", "failure_kind": "transient"}, "retry")
    broker.publish(BrokerMessage(task.task_id))
    worker = Worker(store, broker, max_attempts=3)
    worker.run_once(); assert store.get(task.task_id).status.value == "retrying"
    worker.run_once(); worker.run_once()
    assert store.get(task.task_id).status.value == "failed"
    assert len(broker.dead_letters) == 1
    assert broker.nack_delays == [1, 2]


def test_permanent_failure_goes_directly_to_dlq():
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["triage"], "fail_step": "triage"}, "fatal")
    broker.publish(BrokerMessage(task.task_id))
    Worker(store, broker).run_once()
    assert store.get(task.task_id).status.value == "failed"
    assert len(broker.dead_letters) == 1


def test_claimed_task_cannot_be_processed_concurrently():
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["triage"]}, "claim")
    broker.publish(BrokerMessage(task.task_id))
    handle = broker.consume()
    assert store.claim(task.task_id, "other-worker")
    Worker(store, broker).process(handle)
    assert store.get(task.task_id).status.value == "running"
    assert not broker.dead_letters


def test_cancel_running_task_stops_before_next_step():
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["first", "second"]}, "cancel-running")
    broker.publish(BrokerMessage(task.task_id))
    worker = Worker(store, broker, runner=lambda payload, step: (store.cancel(task.task_id), {"step": step})[1])
    worker.run_once()
    assert store.get(task.task_id).status.value == "cancelled"
    assert store.effect(task.task_id, "1:first") is not None
    assert store.effect(task.task_id, "2:second") is None


def test_fake_runner_rejects_unsafe_or_unbounded_delay():
    for value in [-1, 21, True, "2"]:
        try:
            FakeRunner()({"step_delay_seconds": value}, "step")
        except PermanentFailure:
            continue
        raise AssertionError(f"unsafe delay accepted: {value!r}")


def test_long_step_renews_store_lease_and_broker_visibility():
    import time

    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["long"], "step_delay_seconds": 0.14}, "long-step-heartbeat")
    broker.publish(BrokerMessage(task.task_id))
    heartbeat_calls = []
    visibility_calls = []
    original_heartbeat = store.heartbeat
    original_extend = broker.extend_visibility

    def record_heartbeat(task_id, worker_id):
        heartbeat_calls.append(time.monotonic())
        return original_heartbeat(task_id, worker_id)

    def record_visibility(handle, seconds):
        visibility_calls.append(time.monotonic())
        return original_extend(handle, seconds)

    store.heartbeat = record_heartbeat
    broker.extend_visibility = record_visibility
    worker = Worker(store, broker, heartbeat_interval_seconds=0.02, visibility_timeout_seconds=1)
    assert worker.run_once()
    assert len(heartbeat_calls) >= 2
    assert len(visibility_calls) >= 2
    assert store.get(task.task_id).status.value == "done"


def test_competing_worker_cannot_claim_during_long_running_step():
    import time

    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["long"]}, "long-step-claim")
    broker.publish(BrokerMessage(task.task_id))
    claim_results = []

    def slow_runner(payload, step):
        time.sleep(0.12)
        claim_results.append(store.claim(task.task_id, "competitor"))
        return {"step": step}

    Worker(store, broker, runner=slow_runner, heartbeat_interval_seconds=0.02, visibility_timeout_seconds=1).run_once()
    assert claim_results == [False]
    assert store.get(task.task_id).status.value == "done"


def test_trace_context_reaches_step_thread_and_failure_text_is_not_persisted():
    import asyncio
    import httpx
    from opentelemetry import trace
    from supportops_async.api import create_app
    from supportops_async.tracing import extract_trace_context

    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    parent = extract_trace_context({"traceparent": traceparent})
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["triage"]}, "safe-error")
    broker.publish(BrokerMessage(task.task_id, traceparent))
    observed = []

    def fail(payload, step):
        observed.append(trace.get_current_span().get_span_context().trace_id)
        raise RuntimeError("PRIVATE PROVIDER RESPONSE")

    with trace.use_span(trace.get_tracer("test").start_span("parent", context=parent), end_on_exit=True):
        Worker(store, broker, runner=fail).run_once()
    assert observed == [int("4bf92f3577b34da6a3ce929d0e0e4736", 16)]
    assert store.get(task.task_id).error == "worker_failure"
    assert "PRIVATE PROVIDER RESPONSE" not in repr(store.pending_events())

    async def read_task():
        app = create_app(store, broker)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/tasks/{task.task_id}")
            assert response.json()["error"] == "worker_failure"
            assert "PRIVATE PROVIDER RESPONSE" not in response.text

    asyncio.run(read_task())


def test_worker_cli_logs_only_allowlisted_failure_category(monkeypatch):
    import sys
    from types import SimpleNamespace
    import pytest
    monkeypatch.setitem(sys.modules, "supportops_async.api.runtime", SimpleNamespace(runtime_components=lambda: (object(), object(), None)))
    from supportops_async.worker import cli

    class StopAfterFailure:
        calls = 0
        def __init__(self, *args, **kwargs): pass
        def run_once(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("PRIVATE DATABASE DETAIL")
            raise KeyboardInterrupt
        def flush_events(self): return 0

    output = []
    monkeypatch.setattr(cli, "Worker", StopAfterFailure)
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)
    monkeypatch.setattr(cli.logging, "error", lambda *args, **kwargs: output.append((args, kwargs)))
    with pytest.raises(KeyboardInterrupt):
        cli.main()
    assert len(output) == 1
    assert output[0][0][1] == "worker_failure"
    assert "PRIVATE DATABASE DETAIL" not in repr(output)
