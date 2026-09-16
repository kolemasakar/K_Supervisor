from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ComponentHealth:
    name: str
    ready: bool
    required: bool = True
    detail: str | None = None


@dataclass(frozen=True)
class HealthReport:
    live: bool
    components: tuple[ComponentHealth, ...]


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    components: tuple[ComponentHealth, ...]


class ServiceHealthEvaluator:
    def __init__(self, probes: dict[str, tuple[Callable[[], bool], bool]] | None = None):
        self.probes = probes or {}

    def health(self) -> HealthReport:
        return HealthReport(True, self._components())

    def readiness(self) -> ReadinessReport:
        components = self._components()
        return ReadinessReport(all(item.ready for item in components if item.required), components)

    def _components(self) -> tuple[ComponentHealth, ...]:
        items = []
        for name, (probe, required) in sorted(self.probes.items()):
            try:
                ready = bool(probe())
                detail = None
            except Exception as exc:
                ready = False
                detail = type(exc).__name__
            items.append(ComponentHealth(name=name, ready=ready, required=required, detail=detail))
        return tuple(items)
