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
