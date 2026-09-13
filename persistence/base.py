from __future__ import annotations

from abc import ABC, abstractmethod

from models.agent import AgentRunResult
from models.artifact import ArtifactReference
from models.lifecycle import ProjectLifecycleTransition
from models.operational import ProjectOperationalTransition
from models.project import Project, ProjectSpec
from models.release import Release
from models.task import Task, WorkflowRun


class PersistenceConflictError(RuntimeError):
    pass


class PersistenceStore(ABC):
    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def save_project(self, value: Project) -> None: ...

    @abstractmethod
    def get_project(self, project_id: str) -> Project | None: ...

    @abstractmethod
    def list_projects(self) -> tuple[Project, ...]: ...

    @abstractmethod
    def save_project_spec(self, value: ProjectSpec) -> None: ...

    @abstractmethod
    def get_project_spec(self, project_spec_id: str) -> ProjectSpec | None: ...

    @abstractmethod
    def list_project_specs(self, project_id: str) -> tuple[ProjectSpec, ...]: ...

    @abstractmethod
    def append_lifecycle_transition(self, value: ProjectLifecycleTransition) -> None: ...

    @abstractmethod
    def list_lifecycle_transitions(self, project_id: str) -> tuple[ProjectLifecycleTransition, ...]: ...

    @abstractmethod
    def append_operational_transition(self, value: ProjectOperationalTransition) -> None: ...

    @abstractmethod
    def list_operational_transitions(self, project_id: str) -> tuple[ProjectOperationalTransition, ...]: ...

    @abstractmethod
    def save_task(self, value: Task) -> None: ...

    @abstractmethod
    def get_task(self, task_id: str) -> Task | None: ...

    @abstractmethod
    def list_tasks(self, project_id: str) -> tuple[Task, ...]: ...

    @abstractmethod
    def save_workflow_run(self, value: WorkflowRun) -> None: ...

    @abstractmethod
    def list_workflow_runs(self, project_id: str) -> tuple[WorkflowRun, ...]: ...

    @abstractmethod
    def save_agent_run(self, value: AgentRunResult) -> None: ...

    @abstractmethod
    def list_agent_runs(self, project_id: str) -> tuple[AgentRunResult, ...]: ...

    @abstractmethod
    def save_artifact(self, value: ArtifactReference) -> None: ...

    @abstractmethod
    def list_artifacts(self, project_id: str) -> tuple[ArtifactReference, ...]: ...

    @abstractmethod
    def save_release(self, value: Release) -> None: ...

    @abstractmethod
    def list_releases(self, project_id: str) -> tuple[Release, ...]: ...
