from __future__ import annotations

from typing import Any

from pydantic import Field

from models.base import ContractModel
from models.enums import ProjectLifecycleState, ProjectOperationalState


API_VERSION = "v1"
READ_SCOPE = "projects:read"
LIFECYCLE_WRITE_SCOPE = "projects:lifecycle:write"
OPERATIONAL_WRITE_SCOPE = "projects:operational:write"


class ServicePrincipal(ContractModel):
    principal_id: str = Field(min_length=1, max_length=200)
    scopes: frozenset[str] = frozenset()


class LifecycleTransitionRequest(ContractModel):
    to_state: ProjectLifecycleState
    reason: str = Field(min_length=1, max_length=1000)
    trigger: str = Field(min_length=1, max_length=200)


class OperationalTransitionRequest(ContractModel):
    to_state: ProjectOperationalState


class ApiResponse(ContractModel):
    status_code: int
    body: dict[str, Any]
    headers: dict[str, str] = Field(default_factory=dict)
