import pytest

from supportops_async.store.models import TaskStatus
from supportops_async.store.sqlite import InvalidTransition, SQLiteTaskStore


def test_idempotency_and_stable_task_id_even_for_changed_payload():
    store = SQLiteTaskStore()
    first, created = store.create({"customer": 1}, "request-1")
    replay, replayed_created = store.create({"customer": 99}, "request-1")
    assert created and not replayed_created
    assert replay.task_id == first.task_id
    assert replay.payload == {"customer": 1}


def test_idempotency_key_has_size_and_blank_boundaries():
    store = SQLiteTaskStore()
    for key in ("", "  ", "x" * 201):
        with pytest.raises(ValueError):
            store.create({}, key)


def test_two_connections_racing_same_key_return_one_task(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    path = tmp_path / "race.db"
    first_store, second_store = SQLiteTaskStore(path), SQLiteTaskStore(path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda pair: pair[0].create({"source": pair[1]}, "race-key"), [(first_store, 1), (second_store, 2)]))
    assert results[0][0].task_id == results[1][0].task_id
    assert sum(created for _, created in results) == 1


def test_status_transitions_and_cancellation_are_bounded():
    store = SQLiteTaskStore()
    task, _ = store.create({}, "cancel-me")
    assert store.cancel(task.task_id)
    assert store.get(task.task_id).status is TaskStatus.CANCELLED
    assert not store.claim(task.task_id, "worker")
    with pytest.raises(InvalidTransition):
        store.complete(task.task_id, {})


def test_effect_and_checkpoint_are_durable_and_unique(tmp_path):
    path = tmp_path / "tasks.db"
    store = SQLiteTaskStore(path)
    task, _ = store.create({}, "effect-1")
    assert store.claim(task.task_id, "worker")
    assert store.apply_effect(task.task_id, "1:charge", {"count": 1}) == {"count": 1}
    assert store.apply_effect(task.task_id, "1:charge", {"count": 2}) == {"count": 1}
    store.close()
    reopened = SQLiteTaskStore(path)
    assert reopened.effect(task.task_id, "1:charge") == {"count": 1}
    assert reopened.get(task.task_id).step == "1:charge"


def test_heartbeat_prevents_expired_worker_claim_and_stale_lease_recovers():
    import time

    store = SQLiteTaskStore(lease_seconds=0.02)
    task, _ = store.create({}, "lease-1")
    assert store.claim(task.task_id, "worker-a")
    assert not store.claim(task.task_id, "worker-b")
    assert store.heartbeat(task.task_id, "worker-a")
    time.sleep(0.025)
    assert store.claim(task.task_id, "worker-b")
