from __future__ import annotations

import logging
import time

from supportops_async.api.runtime import runtime_components
from supportops_async.worker import Worker


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    store, broker, events = runtime_components()
    worker = Worker(store, broker, event_publisher=events)
    while True:
        try:
            worked = worker.run_once()
            if not worked:
                worker.flush_events()
        except Exception:
            logging.exception("worker iteration failed; message visibility or durable outbox will permit retry")
            time.sleep(1)


if __name__ == "__main__":
    main()
