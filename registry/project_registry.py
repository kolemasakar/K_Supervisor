from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models.agent import AgentRunResult
from models.artifact import ArtifactReference
from models.audit import AuditEvent
from models.base import ensure_tz
from models.control import RuntimeIdempotencyRecord, ServiceMutationRecord
from models.side_effect import SideEffectExecutionRecord
from models.enums import ProjectLifecycleState, ProjectOperationalState, ProjectSpecStatus
from models.intervention import (
    HumanActionRequest,
    NotificationDeliveryAttempt,
    NotificationEvent,
)
from models.lifecycle import ProjectLifecycleTransition
from models.observability_records import RoutingRecord, ReleaseValidationRecord
from models.operational import ProjectOperationalTransition
from models.project import Project, ProjectSpec
from models.release import Release, ReleaseTarget
from models.task import Task, WorkflowRun
from observability.audit import build_audit_event
from persistence.base import PersistenceStore
from policy.contracts import ApprovalRecord, PolicyDecision


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
    release_targets: tuple[ReleaseTarget, ...] = ()
    human_actions: tuple[HumanActionRequest, ...] = ()
    notifications: tuple[NotificationEvent, ...] = ()
    notification_delivery_attempts: tuple[NotificationDeliveryAttempt, ...] = ()
    approvals: tuple[ApprovalRecord, ...] = ()
    runtime_idempotency: tuple[RuntimeIdempotencyRecord, ...] = ()
    service_mutations: tuple[ServiceMutationRecord, ...] = ()
    side_effect_executions: tuple[SideEffectExecutionRecord, ...] = ()
    policy_decisions: tuple[PolicyDecision, ...] = ()
    audit_events: tuple[AuditEvent, ...] = ()
    routing_records: tuple[RoutingRecord, ...] = ()
    release_validation_records: tuple[ReleaseValidationRecord, ...] = ()


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
        audit = build_audit_event(
            project_id=project_id,
            category="PROJECT",
            event_type="PROJECT_SPEC_ACTIVATED",
            occurred_at=at,
            resource_type="ProjectSpec",
            resource_id=spec.project_spec_id,
        )
        self.store.save_project_with_audit(updated, audit)
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
        audit = build_audit_event(
            project_id=project_id,
            category="PROJECT",
            event_type="PROJECT_LIFECYCLE_TRANSITION",
            occurred_at=at,
            resource_type="Project",
            resource_id=project_id,
            details={
                "from_state": project.lifecycle_state.value,
                "to_state": to_state.value,
                "trigger": trigger,
                "reason": reason,
            },
        )
        self.store.apply_lifecycle_transition(updated, transition, audit)
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
        audit = build_audit_event(
            project_id=project_id,
            category="PROJECT",
            event_type="PROJECT_OPERATIONAL_TRANSITION",
            occurred_at=at,
            resource_type="Project",
            resource_id=project_id,
            details={
                "from_state": project.operational_state.value,
                "to_state": to_state.value,
            },
        )
        self.store.apply_operational_transition(updated, transition, audit)
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
            release_targets=self.store.list_release_targets(project_id),
            human_actions=self.store.list_human_actions(project_id),
            notifications=self.store.list_notifications(project_id),
            notification_delivery_attempts=self.store.list_notification_delivery_attempts(project_id),
            approvals=self.store.list_approvals(project_id),
            runtime_idempotency=self.store.list_runtime_idempotency(project_id),
            service_mutations=self.store.list_service_mutations(project_id),
            side_effect_executions=self.store.list_side_effect_executions(project_id),
            policy_decisions=self.store.list_policy_decisions(project_id),
            audit_events=self.store.list_audit_events(project_id),
            routing_records=self.store.list_routing_records(project_id),
            release_validation_records=self.store.list_release_validation_records(project_id),
        )

    def _require(self, project_id: str) -> Project:
        project = self.store.get_project(project_id)
        if project is None:
            raise KeyError(project_id)
        return project
