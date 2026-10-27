import os
import subprocess
import sys
import time

from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker


def test_process_exit_after_committed_effect_recovers_without_duplicate(tmp_path):
    database = tmp_path / "recovery.db"
    store = SQLiteTaskStore(database, lease_seconds=0.01)
    task, _ = store.create({"steps": ["authorize", "complete"]}, "crash-test")
    task_id = task.task_id
    store.close()
    child = (
        "from supportops_async.store.sqlite import SQLiteTaskStore; import os; "
        f"s=SQLiteTaskStore(r'{database}', lease_seconds=0.01); "
        f"assert s.claim('{task_id}','crashed-worker'); "
        f"s.apply_effect('{task_id}','1:authorize',{{'effect':'once'}}); os._exit(23)"
    )
    crashed = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True)
    assert crashed.returncode == 23
    time.sleep(0.03)
    restarted_store = SQLiteTaskStore(database, lease_seconds=0.01)
    broker = InMemoryBroker()
    broker.publish(BrokerMessage(task_id))
    runner_calls = []
    worker = Worker(restarted_store, broker, runner=lambda payload, step: runner_calls.append(step) or {"step": step})
    worker.run_once()
    assert restarted_store.get(task_id).status.value == "done"
    assert restarted_store.effect(task_id, "1:authorize") == {"effect": "once"}
    assert runner_calls == ["complete"]


def test_recovery_preserves_traceparent_for_remaining_step(tmp_path):
    from opentelemetry import trace

    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    store = SQLiteTaskStore(tmp_path / "trace-recovery.db", lease_seconds=0.01)
    task, _ = store.create({"steps": ["authorize", "complete"]}, "trace-recovery")
    task_id = task.task_id
    store.apply_effect(task_id, "1:authorize", {"effect": "once"})
    store.close()
    time.sleep(0.03)
    restarted_store = SQLiteTaskStore(tmp_path / "trace-recovery.db", lease_seconds=0.01)
    broker = InMemoryBroker()
    broker.publish(BrokerMessage(task_id, traceparent))
    seen = []

    def runner(payload, step):
        seen.append((step, trace.get_current_span().get_span_context().trace_id))
        return {"step": step}

    Worker(restarted_store, broker, runner=runner).run_once()
    assert seen == [("complete", int("4bf92f3577b34da6a3ce929d0e0e4736", 16))]
    assert restarted_store.effect(task_id, "1:authorize") == {"effect": "once"}

