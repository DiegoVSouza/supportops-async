from __future__ import annotations

import logging
import time

from supportops_async.api.runtime import runtime_components
from supportops_async.worker import Worker
from supportops_async.tracing import safe_error_code


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    store, broker, events = runtime_components()
    worker = Worker(store, broker, event_publisher=events)
    while True:
        try:
            worked = worker.run_once()
            if not worked:
                worker.flush_events()
        except Exception as exc:
            logging.error("worker iteration failed; category=%s; durable queue state permits retry", safe_error_code(exc))
            time.sleep(1)


if __name__ == "__main__":
    main()
