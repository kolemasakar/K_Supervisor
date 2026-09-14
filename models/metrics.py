from datetime import datetime
from pydantic import Field, field_validator
from .base import ContractModel, ensure_tz


class AgentMetrics(ContractModel):
    agent_id: str
    runs_total: int = Field(ge=0)
    succeeded: int = Field(ge=0)
    failed: int = Field(ge=0)
    blocked: int = Field(ge=0)
    timed_out: int = Field(ge=0)
    cancelled: int = Field(ge=0)
    success_rate: float = Field(ge=0.0, le=1.0)


class ProjectMetrics(ContractModel):
    project_id: str
    generated_at: datetime
    lifecycle_transitions: int = Field(ge=0)
    operational_transitions: int = Field(ge=0)
    tasks_total: int = Field(ge=0)
    tasks_succeeded: int = Field(ge=0)
    tasks_failed: int = Field(ge=0)
    tasks_blocked: int = Field(ge=0)
    agent_runs_total: int = Field(ge=0)
    routing_records: int = Field(ge=0)
    human_actions_total: int = Field(ge=0)
    human_actions_open: int = Field(ge=0)
    notifications_total: int = Field(ge=0)
    deliveries_sent: int = Field(ge=0)
    deliveries_failed: int = Field(ge=0)
    releases_total: int = Field(ge=0)
    release_validations: int = Field(ge=0)
    audit_events_total: int = Field(ge=0)
    agents: tuple[AgentMetrics, ...] = ()

    @field_validator("generated_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)
