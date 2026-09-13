from __future__ import annotations

from pydantic import field_validator, model_validator

from models.agent import AgentDescriptor
from models.base import ContractModel, JsonObject
from models.capability import CapabilityDescriptor


class CapabilityBlueprint(ContractModel):
    capability_id: str
    capability_version: str = "1.0.0"
    description: str
    operations: tuple[str, ...]
    input_schema: str
    output_schema: str
    constraints: JsonObject = {}
    requires: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ("NONE",)
    risk_class: str = "LOW"
    metadata: JsonObject = {}

    @model_validator(mode="after")
    def validate_blueprint(self):
        if not self.operations:
            raise ValueError("capability blueprint requires at least one operation")
        if "NONE" in self.side_effects and len(self.side_effects) > 1:
            raise ValueError("NONE cannot be combined with other side effects")
        return self


class AgentBlueprint(ContractModel):
    agent_id: str
    agent_type: str
    agent_version: str = "1.0.0"
    contract_version: str = "1.0"
    display_name: str
    class_name: str
    capabilities: tuple[CapabilityBlueprint, ...]
    execution_mode: str = "LOCAL"
    status: str = "AVAILABLE"
    metadata: JsonObject = {}

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, value: str) -> str:
        if not value.isidentifier():
            raise ValueError("class_name must be a valid Python identifier")
        return value

    @model_validator(mode="after")
    def validate_capabilities(self):
        if not self.capabilities:
            raise ValueError("agent blueprint requires at least one capability")
        keys = [(item.capability_id, item.capability_version) for item in self.capabilities]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate capability blueprint")
        return self


class AgentBuild(ContractModel):
    agent: AgentDescriptor
    capabilities: tuple[CapabilityDescriptor, ...]


class ScaffoldFile(ContractModel):
    path: str
    content: str


class ScaffoldValidationReport(ContractModel):
    valid: bool
    checked_files: tuple[str, ...]
    errors: tuple[str, ...] = ()
