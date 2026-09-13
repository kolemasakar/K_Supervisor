from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models.agent import AgentRunResult
from models.artifact import ArtifactReference
from models.base import ensure_tz
from models.enums import ProjectLifecycleState, ProjectOperationalState, ProjectSpecStatus
from models.lifecycle import ProjectLifecycleTransition
from models.operational import ProjectOperationalTransition
from models.project import Project, ProjectSpec
from models.release import Release
from models.task import Task, WorkflowRun
from persistence.base import PersistenceStore


class ProjectRecoverySnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    project: Project
    active_spec: ProjectSpec | None
    specs: tuple[ProjectSpec, ...]
    lifecycle_transitions: tuple[ProjectLifecycleTransition, ...]
    operational_transitions: tuple[ProjectOperationalTransition, ...]
    tasks: tuple[Task, ...]
    workflow_runs: tuple[WorkflowRun, ...]
    agent_runs: tuple[AgentRunResult, ...]
    artifacts: tuple[ArtifactReference, ...]
    releases: tuple[Release, ...]


class ProjectRegistry:
    def __init__(self, store: PersistenceStore):
        self.store = store

    def register(self, project: Project, spec: ProjectSpec | None = None) -> Project:
        if spec is not None and spec.project_id != project.project_id:
            raise ValueError("ProjectSpec project_id does not match Project")
        if spec is not None:
            self.store.save_project_spec(spec)
        if project.active_project_spec_id is not None:
            valid = (
                spec is not None
                and spec.project_spec_id == project.active_project_spec_id
                and spec.status == ProjectSpecStatus.APPROVED
            )
            if not valid:
                raise ValueError("active_project_spec_id requires matching approved ProjectSpec")
        self.store.save_project(project)
        return project

    def get(self, project_id: str) -> Project | None:
        return self.store.get_project(project_id)

    def list(self) -> tuple[Project, ...]:
        return self.store.list_projects()

    def add_spec(self, spec: ProjectSpec) -> None:
        if self.store.get_project(spec.project_id) is None:
            raise KeyError(spec.project_id)
        self.store.save_project_spec(spec)

    def activate_spec(self, project_id: str, spec: ProjectSpec, at: datetime) -> Project:
        project = self._require(project_id)
        at = ensure_tz(at)
        if spec.project_id != project_id:
            raise ValueError("ProjectSpec project_id does not match Project")
        if spec.status != ProjectSpecStatus.APPROVED:
            raise ValueError("only APPROVED ProjectSpec can be activated")
        self.store.save_project_spec(spec)
        updated = project.model_copy(
            update={"active_project_spec_id": spec.project_spec_id, "updated_at": at}
        )
        self.store.save_project(updated)
        return updated

    def transition_lifecycle(
        self,
        project_id: str,
        to_state: ProjectLifecycleState,
        reason: str,
        trigger: str,
        at: datetime,
    ) -> Project:
        project = self._require(project_id)
        at = ensure_tz(at)
        transition = ProjectLifecycleTransition(
            project_id=project_id,
            from_state=project.lifecycle_state,
            to_state=to_state,
            reason=reason,
            trigger=trigger,
            timestamp=at,
        )
        updated = project.model_copy(
            update={"lifecycle_state": to_state, "updated_at": at}
        )
        self.store.apply_lifecycle_transition(updated, transition)
        return updated

    def transition_operational(
        self,
        project_id: str,
        to_state: ProjectOperationalState,
        at: datetime,
    ) -> Project:
        project = self._require(project_id)
        at = ensure_tz(at)
        transition = ProjectOperationalTransition(
            project_id=project_id,
            from_state=project.operational_state,
            to_state=to_state,
            timestamp=at,
        )
        updated = project.model_copy(
            update={"operational_state": to_state, "updated_at": at}
        )
        self.store.apply_operational_transition(updated, transition)
        return updated

    def recover(self, project_id: str) -> ProjectRecoverySnapshot:
        project = self._require(project_id)
        specs = self.store.list_project_specs(project_id)
        active_spec = (
            self.store.get_project_spec(project.active_project_spec_id)
            if project.active_project_spec_id
            else None
        )
        return ProjectRecoverySnapshot(
            project=project,
            active_spec=active_spec,
            specs=specs,
            lifecycle_transitions=self.store.list_lifecycle_transitions(project_id),
            operational_transitions=self.store.list_operational_transitions(project_id),
            tasks=self.store.list_tasks(project_id),
            workflow_runs=self.store.list_workflow_runs(project_id),
            agent_runs=self.store.list_agent_runs(project_id),
            artifacts=self.store.list_artifacts(project_id),
            releases=self.store.list_releases(project_id),
        )

    def _require(self, project_id: str) -> Project:
        project = self.store.get_project(project_id)
        if project is None:
            raise KeyError(project_id)
        return project
