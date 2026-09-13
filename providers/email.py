from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OutboundEmail:
    recipient: str
    subject: str
    body: str


class EmailProvider(Protocol):
    def send(self, message: OutboundEmail, idempotency_key: str) -> str | None: ...
