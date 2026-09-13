from __future__ import annotations

from dataclasses import dataclass

from models.base import ContractModel, JsonObject
from models.release import Release, ReleaseTarget


class ReleaseCheckResult(ContractModel):
    check_id: str
    passed: bool
    summary: str
    required: bool = True
    metadata: JsonObject = {}


class ReleaseReadinessReport(ContractModel):
    release_id: str
    project_id: str
    target_type: str
    checks: tuple[ReleaseCheckResult, ...]

    @property
    def ready(self) -> bool:
        return all(item.passed for item in self.checks if item.required)


@dataclass(frozen=True)
class ReleaseEvidence:
    available_files: tuple[str, ...] = ()
    satisfied_criteria: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReleasePreparationOutcome:
    release: Release
    targets: tuple[ReleaseTarget, ...]
    reports: tuple[ReleaseReadinessReport, ...]
