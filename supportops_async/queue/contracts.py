from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class BrokerMessage:
    task_id: str


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
