import time
from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker


def test_early_redelivery_is_deferred_until_database_lease_expires():
    store=SQLiteTaskStore(lease_seconds=.03)
    broker=InMemoryBroker()
    task,_=store.create({"steps":["finish"]},"early-redelivery")
    assert store.claim(task.task_id,"dead-worker")
    broker.publish(BrokerMessage(task.task_id))
    worker=Worker(store,broker,worker_id="recovery-worker")
    assert worker.run_once()
    assert broker.nack_delays, "failed claim must preserve the surviving SQS message"
    time.sleep(.04)
    assert worker.run_once()
    assert store.get(task.task_id).status.value=="done"
