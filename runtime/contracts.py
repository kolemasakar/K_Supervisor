from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event
from typing import Protocol

from models.agent import AgentRunRequest, AgentRunResult

from .errors import RuntimeCancelled, RuntimeLimitExceeded, RuntimeValidationError


@dataclass(frozen=True)
class RuntimeLimits:
    timeout_seconds: float | None = None
    max_tool_calls: int | None = None
    max_tokens: int | None = None
    max_sources: int | None = None
    max_cost: float | None = None
    max_retries: int | None = None

    @classmethod
    def from_request(cls, values: dict) -> "RuntimeLimits":
        known = {
            "timeout_seconds",
            "max_tool_calls",
            "max_tokens",
            "max_sources",
            "max_cost",
            "max_retries",
        }
        unknown = set(values) - known
        if unknown:
            raise RuntimeValidationError(
                f"unsupported runtime limits: {', '.join(sorted(unknown))}"
            )

        timeout = values.get("timeout_seconds")
        if timeout is not None and (
            not isinstance(timeout, (int, float))
            or isinstance(timeout, bool)
            or timeout <= 0
        ):
            raise RuntimeValidationError("timeout_seconds must be > 0")

        parsed: dict[str, int | float | None] = {"timeout_seconds": timeout}
        for name in ("max_tool_calls", "max_tokens", "max_sources", "max_retries"):
            value = values.get(name)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise RuntimeValidationError(f"{name} must be a non-negative integer")
            parsed[name] = value

        cost = values.get("max_cost")
        if cost is not None and (
            not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0
        ):
            raise RuntimeValidationError("max_cost must be non-negative")
        parsed["max_cost"] = float(cost) if cost is not None else None
        return cls(**parsed)


@dataclass
class ExecutionControl:
    limits: RuntimeLimits
    cancelled: Event = field(default_factory=Event)
    usage: dict[str, float] = field(default_factory=dict)

    def cancel(self) -> None:
        self.cancelled.set()

    def check_cancelled(self) -> None:
        if self.cancelled.is_set():
            raise RuntimeCancelled("execution cancelled")

    def consume(self, resource: str, amount: int | float = 1) -> None:
        self.check_cancelled()
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            raise RuntimeValidationError("resource consumption must be non-negative numeric")
        limit_name = {
            "tool_calls": "max_tool_calls",
            "tokens": "max_tokens",
            "sources": "max_sources",
            "cost": "max_cost",
        }.get(resource)
        if limit_name is None:
            raise RuntimeValidationError(f"unsupported runtime resource: {resource}")
        current = self.usage.get(resource, 0.0) + float(amount)
        limit = getattr(self.limits, limit_name)
        if limit is not None and current > float(limit):
            raise RuntimeLimitExceeded(f"{resource} limit exceeded")
        self.usage[resource] = current


class RuntimeAdapter(Protocol):
    def execute(
        self,
        request: AgentRunRequest,
        control: ExecutionControl,
    ) -> AgentRunResult: ...
