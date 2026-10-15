from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker


def main() -> None:
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create(
        {"operation_id": "demo-2026-01", "ticket_id": "T-100", "steps": ["triage", "draft_reply"]},
        "demo-request-1",
    )
    broker.publish(BrokerMessage(task.task_id))
    Worker(store, broker).run_once()
    print(store.get(task.task_id))


if __name__ == "__main__":
    main()
