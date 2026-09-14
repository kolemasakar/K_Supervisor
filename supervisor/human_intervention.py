from datetime import datetime

from models.audit import AuditEvent
from models.base import ensure_tz
from models.enums import HumanActionStatus, ProjectOperationalState
from models.intervention import HumanActionRequest
from models.operational import ProjectOperationalTransition
from observability.audit import build_audit_event
from persistence.base import PersistenceStore
from registry.project_registry import ProjectRegistry


class HumanInterventionBroker:
    def __init__(self, store: PersistenceStore, registry: ProjectRegistry):
        self.store = store
        self.registry = registry

    def open(self, action: HumanActionRequest) -> HumanActionRequest:
        project = self.registry.get(action.project_id)
        if project is None:
            raise KeyError(action.project_id)
        state = HumanActionStatus.WAITING_FOR_OWNER if action.blocking else HumanActionStatus.OPEN
        saved = action.model_copy(update={"status": state})
        audit = self._audit_event(saved, "HUMAN_ACTION_OPENED", action.created_at)
        if not action.blocking or project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER:
            self.store.save_human_action(saved, audit)
            return saved

        transition = ProjectOperationalTransition(
            project_id=project.project_id,
            from_state=project.operational_state,
            to_state=ProjectOperationalState.WAITING_FOR_OWNER,
            timestamp=action.created_at,
        )
        updated_project = project.model_copy(
            update={
                "operational_state": ProjectOperationalState.WAITING_FOR_OWNER,
                "updated_at": action.created_at,
            }
        )
        self.store.apply_human_action_operational_transition(
            saved,
            updated_project,
            transition,
            audit,
        )
        return saved

    def verify(self, human_action_id: str, ok: bool, at: datetime) -> HumanActionRequest:
        at = ensure_tz(at)
        action = self.store.get_human_action(human_action_id)
        if action is None:
            raise KeyError(human_action_id)
        if action.status == HumanActionStatus.VERIFIED or not ok:
            return action
        resolved = action.model_copy(
            update={"status": HumanActionStatus.VERIFIED, "resolved_at": at}
        )
        audit = self._audit_event(resolved, "HUMAN_ACTION_VERIFIED", at)
        return self._resolve(action, resolved, at, audit)

    def cancel(self, human_action_id: str, at: datetime) -> HumanActionRequest:
        at = ensure_tz(at)
        action = self.store.get_human_action(human_action_id)
        if action is None:
            raise KeyError(human_action_id)
        if action.status == HumanActionStatus.CANCELLED:
            return action
        if action.status == HumanActionStatus.VERIFIED:
            raise ValueError("verified human action cannot be cancelled")
        resolved = action.model_copy(
            update={"status": HumanActionStatus.CANCELLED, "resolved_at": at}
        )
        audit = self._audit_event(resolved, "HUMAN_ACTION_CANCELLED", at)
        return self._resolve(action, resolved, at, audit)

    def _resolve(
        self,
        original: HumanActionRequest,
        resolved: HumanActionRequest,
        at: datetime,
        audit: AuditEvent,
    ) -> HumanActionRequest:
        blockers = [
            item
            for item in self.store.list_human_actions(original.project_id)
            if item.human_action_id != original.human_action_id
            and item.blocking
            and item.status not in {HumanActionStatus.VERIFIED, HumanActionStatus.CANCELLED}
        ]
        project = self.registry.get(original.project_id)
        if project is None:
            raise KeyError(original.project_id)
        if original.blocking and not blockers and project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER:
            transition = ProjectOperationalTransition(
                project_id=project.project_id,
                from_state=ProjectOperationalState.WAITING_FOR_OWNER,
                to_state=ProjectOperationalState.ACTIVE,
                timestamp=at,
            )
            updated_project = project.model_copy(
                update={"operational_state": ProjectOperationalState.ACTIVE, "updated_at": at}
            )
            self.store.apply_human_action_operational_transition(
                resolved,
                updated_project,
                transition,
                audit,
            )
        else:
            self.store.save_human_action(resolved, audit)
        return resolved

    @staticmethod
    def _audit_event(
        action: HumanActionRequest,
        event_type: str,
        at: datetime,
    ) -> AuditEvent:
        return build_audit_event(
            project_id=action.project_id,
            category="INTERVENTION",
            event_type=event_type,
            occurred_at=at,
            resource_type="HumanActionRequest",
            resource_id=action.human_action_id,
            severity="WARNING" if action.blocking else "INFO",
            details={
                "action_type": action.action_type,
                "blocking": action.blocking,
                "status": action.status.value,
            },
        )
