from __future__ import annotations

import logging
import os
import signal
import threading
import time

from supportops_async.api.runtime import runtime_components
from supportops_async.worker import Worker
from supportops_async.tracing import safe_error_code
from supportops_async.telemetry import configure_telemetry, shutdown_telemetry


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda _signum, _frame: stop.set())
    signal.signal(signal.SIGINT, lambda _signum, _frame: stop.set())
    provider = configure_telemetry(os.getenv("OTEL_SERVICE_NAME", "supportops-async-worker"))
    try:
        store, broker, events = runtime_components()
        worker = Worker(store, broker, event_publisher=events)
        while not stop.is_set():
            try:
                worked = worker.run_once()
                if not worked:
                    worker.flush_events()
                    stop.wait(1)
            except Exception as exc:
                logging.error("worker iteration failed; category=%s; durable queue state permits retry", safe_error_code(exc))
                stop.wait(1)
    finally:
        if not shutdown_telemetry(provider):
            logging.warning("telemetry shutdown incomplete")


if __name__ == "__main__":
    main()
