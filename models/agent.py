from pydantic import model_validator

from .base import ContractModel, JsonObject
from .capability import validate_capability_id
from .enums import ExecutionStatus


class CapabilityRef(ContractModel):
    capability_id: str
    capability_version: str


class AgentDescriptor(ContractModel):
    agent_id: str
    agent_type: str
    agent_version: str
    contract_version: str = "1.0"
    display_name: str
    capabilities: tuple[CapabilityRef, ...]
    execution_mode: str = "LOCAL"
    status: str = "REGISTERED"
    metadata: JsonObject = {}


class AgentRunRequest(ContractModel):
    request_id: str
    project_id: str
    task_id: str
    workflow_run_id: str
    run_id: str
    agent_id: str
    capability_id: str
    capability_version: str
    operation: str
    input: JsonObject
    context: JsonObject = {}
    policy: JsonObject = {}
    limits: JsonObject = {}
    idempotency_key: str | None = None
    metadata: JsonObject = {}

    @model_validator(mode="after")
    def validate_capability(self):
        validate_capability_id(self.capability_id)
        return self


class AgentError(ContractModel):
    code: str
    category: str
    message: str
    retryable: bool = False
    details: JsonObject = {}


class AgentRunResult(ContractModel):
    request_id: str
    project_id: str
    task_id: str
    workflow_run_id: str
    run_id: str
    agent_id: str
    capability_id: str
    capability_version: str
    status: ExecutionStatus
    output: JsonObject = {}
    artifacts: tuple[str, ...] = ()
    metrics: JsonObject = {}
    error: AgentError | None = None
    warnings: tuple[str, ...] = ()
    metadata: JsonObject = {}

    @model_validator(mode="after")
    def validate_result(self):
        validate_capability_id(self.capability_id)
        if self.status == ExecutionStatus.FAILED and self.error is None:
            raise ValueError("failed result requires error")
        return self
