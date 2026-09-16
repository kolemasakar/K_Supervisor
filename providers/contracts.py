from __future__ import annotations

from typing import Protocol

from access import AccessReference
from integrations import AvailabilityReport, DependencyRequirement
from models.base import ContractModel, JsonObject


class ModelProfile(ContractModel):
    model_id: str
    features: tuple[str, ...] = ()
    context_window: int | None = None
    priority: int = 0
    metadata: JsonObject = {}


class ProviderDescriptor(ContractModel):
    provider_id: str
    version: str
    provider_type: str
    operations: tuple[str, ...] = ()
    dependencies: tuple[DependencyRequirement, ...] = ()
    models: tuple[ModelProfile, ...] = ()
    metadata: JsonObject = {}


class ProviderRequest(ContractModel):
    project_id: str
    operation: str
    payload: JsonObject = {}
    access_refs: tuple[AccessReference, ...] = ()
    request_id: str | None = None
    agent_id: str | None = None
    capability_id: str | None = None
    capability_version: str | None = None
    idempotency_key: str | None = None


class ProviderResponse(ContractModel):
    payload: JsonObject = {}
    metadata: JsonObject = {}


class Provider(Protocol):
    descriptor: ProviderDescriptor

    def check_availability(self) -> AvailabilityReport: ...
    def execute(self, request: ProviderRequest) -> ProviderResponse: ...
