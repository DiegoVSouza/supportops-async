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
