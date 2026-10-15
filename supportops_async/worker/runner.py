from __future__ import annotations

from typing import Any, Callable
import time

from supportops_async.queue.contracts import Broker, MessageHandle
from supportops_async.store.models import TaskStore
from supportops_async.events.events import EventPublisher, drain_outbox


class TransientFailure(RuntimeError):
    pass


class PermanentFailure(RuntimeError):
    pass


class FakeRunner:
    """Deterministic runner for local demos; payload may request controlled failures."""

    def __call__(self, payload: dict[str, Any], step: str) -> dict[str, Any]:
        delay = payload.get("step_delay_seconds", 0)
        if not isinstance(delay, (int, float)) or isinstance(delay, bool) or delay < 0 or delay > 20:
            raise PermanentFailure("step_delay_seconds must be between 0 and 20")
        if delay:
            time.sleep(delay)
        failure = payload.get("fail_step") == step
        if failure:
            if payload.get("failure_kind") == "transient":
                raise TransientFailure("requested transient fake failure")
            raise PermanentFailure("requested permanent fake failure")
        return {"step": step, "outcome": "simulated"}


class Worker:
    def __init__(self, store: TaskStore, broker: Broker, *, runner: Callable[[dict[str, Any], str], dict[str, Any]] | None = None, event_publisher: EventPublisher | None = None, worker_id: str = "worker-1", max_attempts: int = 3, base_delay: int = 1) -> None:
        if max_attempts < 1 or base_delay < 0:
            raise ValueError("max_attempts must be positive and base_delay non-negative")
        self.store, self.broker = store, broker
        self.runner = runner or FakeRunner()
        self.event_publisher = event_publisher
        self.worker_id, self.max_attempts, self.base_delay = worker_id, max_attempts, base_delay

    def run_once(self) -> bool:
        handle = self.broker.consume()
        if handle is None:
            return False
        self.process(handle)
        self.flush_events()
        return True

    def flush_events(self) -> int:
        if self.event_publisher is None:
            return 0
        return drain_outbox(self.store, self.event_publisher)

    def process(self, handle: MessageHandle) -> None:
        task = self.store.get(handle.message.task_id)
        if task is None or task.status.value in {"done", "failed", "cancelled"}:
            self.broker.ack(handle)
            return
        if not self.store.claim(task.task_id, self.worker_id):
            self.broker.ack(handle)
            return
        try:
            steps = task.payload.get("steps", ["triage", "resolve"])
            if not isinstance(steps, list) or not steps or len(steps) > 20 or not all(isinstance(s, str) and s for s in steps):
                raise PermanentFailure("steps must contain 1 to 20 non-empty names")
            results: list[dict[str, Any]] = []
            for index, step in enumerate(steps, start=1):
                current = self.store.get(task.task_id)
                if current is None or current.status.value == "cancelled":
                    self.broker.ack(handle)
                    return
                self.broker.extend_visibility(handle, 30)
                key = f"{index}:{step}"
                prior = self.store.effect(task.task_id, key)
                if prior is not None:
                    result = prior
                else:
                    effect_result = self.runner(task.payload, step)
                    effect_result["effect_key"] = f"{task.payload.get('operation_id', task.task_id)}:{key}"
                    result = self.store.apply_effect(task.task_id, key, effect_result)
                results.append(result)
                self.store.heartbeat(task.task_id, self.worker_id)
            self.store.complete(task.task_id, {"steps": results})
            self.broker.ack(handle)
        except TransientFailure as exc:
            if handle.attempts >= self.max_attempts:
                self.store.fail(task.task_id, str(exc))
                self.broker.dead_letter(handle)
            else:
                self.store.retry(task.task_id)
                self.broker.nack(handle, self.base_delay * (2 ** (handle.attempts - 1)))
        except Exception as exc:
            self.store.fail(task.task_id, str(exc))
            self.broker.dead_letter(handle)
