from pydantic import field_validator, model_validator

from .base import ContractModel, JsonObject


def validate_capability_id(value: str) -> str:
    parts = value.split(".")
    if len(parts) < 2 or any(not part or part.lower() != part for part in parts):
        raise ValueError("invalid capability_id")
    return value


class CapabilityDescriptor(ContractModel):
    capability_id: str
    capability_version: str
    description: str
    operations: tuple[str, ...]
    input_schema: str
    output_schema: str
    constraints: JsonObject = {}
    requires: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ("NONE",)
    risk_class: str = "LOW"
    metadata: JsonObject = {}

    _id = field_validator("capability_id")(validate_capability_id)

    @model_validator(mode="after")
    def validate_contract(self):
        if "NONE" in self.side_effects and len(self.side_effects) > 1:
            raise ValueError("NONE cannot be combined with other side effects")
        if not self.operations:
            raise ValueError("at least one operation is required")
        return self


class CapabilityRequirement(ContractModel):
    capability_id: str
    version_constraint: str
    operation: str
    hard_constraints: JsonObject = {}
    preferences: JsonObject = {}

    _id = field_validator("capability_id")(validate_capability_id)
