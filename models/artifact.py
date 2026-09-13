from datetime import datetime

from pydantic import field_validator

from .base import ContractModel, JsonObject, ensure_tz


class ArtifactReference(ContractModel):
    artifact_id: str
    project_id: str
    uri: str
    media_type: str | None = None
    checksum: str | None = None
    created_at: datetime
    metadata: JsonObject = {}

    @field_validator("created_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)
