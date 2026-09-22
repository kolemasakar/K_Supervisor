from __future__ import annotations

from typing import Any

from pydantic import Field

from models.base import ContractModel, JsonObject
from models.capability import CapabilityRequirement
from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.workflow import WorkflowDefinition


API_VERSION = "v1"

# v0.3 Phase 5 compatibility scopes.
READ_SCOPE = "projects:read"
LIFECYCLE_WRITE_SCOPE = "projects:lifecycle:write"
OPERATIONAL_WRITE_SCOPE = "projects:operational:write"

# v0.4 Phase 2 additive least-privilege scopes.
PROJECT_REGISTER_SCOPE = "projects:register"
PROJECT_SPECS_READ_SCOPE = "project-specs:read"
PROJECT_SPECS_SUBMIT_SCOPE = "project-specs:submit"
PROJECT_SPECS_APPROVE_SCOPE = "project-specs:approve"
PROJECT_SPECS_ACTIVATE_SCOPE = "project-specs:activate"
HUMAN_ACTIONS_READ_SCOPE = "human-actions:read"
HUMAN_ACTIONS_VERIFY_SCOPE = "human-actions:verify"
APPROVALS_READ_SCOPE = "approvals:read"
APPROVALS_DECIDE_SCOPE = "approvals:decide"
EXECUTIONS_READ_SCOPE = "executions:read"
EXECUTIONS_START_SCOPE = "executions:start"
EXECUTIONS_CANCEL_SCOPE = "executions:cancel"
RELEASES_READ_SCOPE = "releases:read"
RELEASES_CONFIRM_SCOPE = "releases:publication:confirm"
RECOVERY_READ_SCOPE = "recovery:read"
REPOSITORY_READ_SCOPE = "repository:read"
REPOSITORY_BOOTSTRAP_SCOPE = "repository:bootstrap"


class ServicePrincipal(ContractModel):
    principal_id: str = Field(min_length=1, max_length=200)
    scopes: frozenset[str] = frozenset()


class LifecycleTransitionRequest(ContractModel):
    to_state: ProjectLifecycleState
    reason: str = Field(min_length=1, max_length=1000)
    trigger: str = Field(min_length=1, max_length=200)


class OperationalTransitionRequest(ContractModel):
    to_state: ProjectOperationalState


class ProjectRegistrationRequest(ContractModel):
    project_id: str = Field(min_length=1, max_length=200)
    spec_version: str = Field(default="0.1", min_length=1, max_length=100)
    onboarding: JsonObject


class ProjectSpecSubmissionRequest(ContractModel):
    spec_version: str = Field(min_length=1, max_length=100)
    onboarding: JsonObject
    supersedes_spec_id: str | None = Field(default=None, max_length=200)


class ApprovalRevokeRequest(ContractModel):
    reason: str = Field(min_length=1, max_length=1000)


class TaskStartRequest(ContractModel):
    title: str = Field(min_length=1, max_length=500)
    requirement: CapabilityRequirement
    input: JsonObject
    context: JsonObject = {}
    policy: JsonObject = {}
    limits: JsonObject = {}


class WorkflowStartRequest(ContractModel):
    title: str = Field(min_length=1, max_length=500)
    definition: WorkflowDefinition
    input: JsonObject
    approvals: dict[str, bool] = {}


class ApiResponse(ContractModel):
    status_code: int
    body: dict[str, Any]
    headers: dict[str, str] = Field(default_factory=dict)
