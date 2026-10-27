from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class BrokerMessage:
    task_id: str
    traceparent: str | None = None

    def __post_init__(self) -> None:
        if self.traceparent is not None:
            from supportops_async.tracing import extract_trace_context, inject_traceparent

            object.__setattr__(self, "traceparent", inject_traceparent(extract_trace_context({"traceparent": self.traceparent})))


@dataclass(frozen=True)
class MessageHandle:
    receipt: str
    message: BrokerMessage
    attempts: int


class Broker(Protocol):
    def publish(self, msg: BrokerMessage) -> None: ...
    def consume(self) -> MessageHandle | None: ...
    def ack(self, handle: MessageHandle) -> None: ...
    def nack(self, handle: MessageHandle, delay: int) -> None: ...
    def extend_visibility(self, handle: MessageHandle, seconds: int) -> None: ...
    def dead_letter(self, handle: MessageHandle) -> None: ...
