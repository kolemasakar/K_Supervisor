from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from models.project import ProjectSpec


@dataclass(frozen=True)
class SchedulerLimits:
    global_max_concurrency: int = 4
    provider_concurrency: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.global_max_concurrency < 1:
            raise ValueError("global_max_concurrency must be >= 1")
        for key, value in self.provider_concurrency.items():
            if not key or value < 1:
                raise ValueError("provider concurrency limits must be positive")


@dataclass(frozen=True)
class ProjectSchedulePolicy:
    priority: int = 0
    max_concurrency: int = 1
    budget_limit: float | None = None

    def __post_init__(self) -> None:
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        if self.budget_limit is not None and self.budget_limit < 0:
            raise ValueError("budget_limit must be non-negative")

    @classmethod
    def from_spec(cls, spec: ProjectSpec) -> "ProjectSchedulePolicy":
        parallel = spec.parallel_execution
        risk = spec.risk
        priority = parallel.get("priority", 0)
        max_concurrency = parallel.get("max_concurrency", 1)
        budget_limit = risk.get("budget_limit", parallel.get("budget_limit"))
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ValueError("parallel_execution.priority must be an integer")
        if not isinstance(max_concurrency, int) or isinstance(max_concurrency, bool):
            raise ValueError("parallel_execution.max_concurrency must be an integer")
        if budget_limit is not None and (
            not isinstance(budget_limit, (int, float)) or isinstance(budget_limit, bool)
        ):
            raise ValueError("budget_limit must be numeric")
        return cls(
            priority=priority,
            max_concurrency=max_concurrency,
            budget_limit=float(budget_limit) if budget_limit is not None else None,
        )


@dataclass(frozen=True)
class SchedulerJob:
    work_id: str
    project_id: str
    execute: Callable[[], Any]
    priority: int = 0
    provider_key: str | None = None
    shared_resources: tuple[str, ...] = ()
    estimated_cost: float = 0.0

    def __post_init__(self) -> None:
        if not self.work_id or not self.project_id:
            raise ValueError("work_id and project_id are required")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise ValueError("priority must be an integer")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be non-negative")
        if len(set(self.shared_resources)) != len(self.shared_resources):
            raise ValueError("shared_resources must be unique")


@dataclass(frozen=True)
class SchedulerSnapshot:
    pending: int
    running_global: int
    running_by_project: dict[str, int]
    provider_running: dict[str, int]
    held_resources: tuple[str, ...]
    budget_used: dict[str, float]
