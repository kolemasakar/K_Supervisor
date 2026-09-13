from __future__ import annotations

from typing import Protocol

from access import AccessReference
from integrations import AvailabilityReport, DependencyRequirement
from models.base import ContractModel, JsonObject


class ToolDescriptor(ContractModel):
    tool_id: str
    version: str
    operations: tuple[str, ...]
    dependencies: tuple[DependencyRequirement, ...] = ()
    metadata: JsonObject = {}


class ToolRequest(ContractModel):
    project_id: str
    operation: str
    input: JsonObject = {}
    access_refs: tuple[AccessReference, ...] = ()


class ToolResult(ContractModel):
    output: JsonObject = {}
    metadata: JsonObject = {}


class Tool(Protocol):
    descriptor: ToolDescriptor

    def check_availability(self) -> AvailabilityReport: ...
    def invoke(self, request: ToolRequest) -> ToolResult: ...
