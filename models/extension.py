from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExtensionSignatureStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class ExtensionTrustRecord(BaseModel):
    """Durable governance decision bound to one exact discovered extension identity."""

    model_config = ConfigDict(frozen=True)

    record_id: str = Field(min_length=1)
    extension_identity: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    name: str = Field(min_length=1)
    group: str = Field(min_length=1)
    value: str = Field(min_length=1)
    distribution: str = Field(min_length=1)
    distribution_version: str = Field(min_length=1)
    platform_constraint: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    enabled: bool = False
    trusted: bool = False
    signature_status: ExtensionSignatureStatus = ExtensionSignatureStatus.UNVERIFIED
    verification_reference: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_signature_evidence(self) -> "ExtensionTrustRecord":
        if self.signature_status == ExtensionSignatureStatus.VERIFIED:
            if self.verification_reference is None or not self.verification_reference.strip():
                raise ValueError("verified extension signature requires verification_reference")
        return self
