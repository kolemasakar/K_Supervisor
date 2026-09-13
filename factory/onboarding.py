from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.base import ensure_tz
from models.enums import ProjectSpecStatus
from models.project import ProjectSpec


def build_draft_project_spec(
    project_id: str,
    onboarding: dict,
    at: datetime,
    *,
    project_spec_id: str | None = None,
    spec_version: str = "0.1",
) -> ProjectSpec:
    at = ensure_tz(at)

    def required(name: str):
        value = onboarding.get(name)
        if value is None or value == "" or value == []:
            raise ValueError(f"missing onboarding field: {name}")
        return value

    name = str(required("name"))
    return ProjectSpec(
        project_spec_id=project_spec_id or f"PSPEC_{uuid4().hex}",
        project_id=project_id,
        spec_version=spec_version,
        status=ProjectSpecStatus.DRAFT,
        created_at=at,
        updated_at=at,
        name=name,
        short_name=str(onboarding.get("short_name") or name),
        purpose=str(required("purpose")),
        problem_statement=str(required("problem_statement")),
        project_type=str(required("project_type")),
        success_criteria=tuple(required("success_criteria")),
        first_working_criteria=tuple(required("first_working_criteria")),
        documentation=dict(onboarding.get("documentation") or {}),
        repository=dict(required("repository")),
        architecture=dict(onboarding.get("architecture") or {}),
        integrations=dict(onboarding.get("integrations") or {}),
        agents=dict(onboarding.get("agents") or {}),
        autonomy=dict(onboarding.get("autonomy") or {}),
        notifications=dict(onboarding.get("notifications") or {"primary_channel": "EMAIL"}),
        parallel_execution=dict(onboarding.get("parallel_execution") or {}),
        release=dict(onboarding.get("release") or {}),
        risk=dict(onboarding.get("risk") or {}),
    )
