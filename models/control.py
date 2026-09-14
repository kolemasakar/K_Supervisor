from __future__ import annotations

from datetime import datetime

from pydantic import field_validator

from .agent import AgentRunResult
from .base import ContractModel, ensure_tz


class RuntimeIdempotencyRecord(ContractModel):
    """Durable successful runtime result keyed by a semantic command scope."""

    record_id: str
    project_id: str
    scope: str
    signature: str
    result: AgentRunResult
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        return ensure_tz(value)
