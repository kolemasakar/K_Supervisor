from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from access import AccessReference
from models.base import ContractModel, JsonObject


class ProvisioningKind(StrEnum):
    REPOSITORY = "REPOSITORY"
    SERVICE = "SERVICE"
    SERVER = "SERVER"
    DATABASE = "DATABASE"
    CLOUD_RESOURCE = "CLOUD_RESOURCE"


class ProvisioningRequest(ContractModel):
    project_id: str
    kind: ProvisioningKind
    provider_id: str
    resource_name: str
    configuration: JsonObject = {}
    access_refs: tuple[AccessReference, ...] = ()


class ProvisioningResult(ContractModel):
    resource_id: str
    locator: str | None = None
    created: bool
    metadata: JsonObject = {}


class ProvisioningAdapter(Protocol):
    provider_id: str
    supported_kinds: tuple[ProvisioningKind, ...]

    def available(self) -> bool: ...
    def provision(self, request: ProvisioningRequest) -> ProvisioningResult: ...
