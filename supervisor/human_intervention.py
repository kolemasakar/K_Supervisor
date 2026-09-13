from datetime import datetime

from models.base import ensure_tz
from models.enums import HumanActionStatus, ProjectOperationalState
from models.intervention import HumanActionRequest
from models.operational import ProjectOperationalTransition
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
        if not action.blocking or project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER:
            self.store.save_human_action(saved)
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
        self.store.apply_human_action_operational_transition(saved, updated_project, transition)
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
        blockers = [
            item
            for item in self.store.list_human_actions(action.project_id)
            if item.human_action_id != human_action_id
            and item.blocking
            and item.status not in {HumanActionStatus.VERIFIED, HumanActionStatus.CANCELLED}
        ]
        project = self.registry.get(action.project_id)
        if project is None:
            raise KeyError(action.project_id)
        if action.blocking and not blockers and project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER:
            transition = ProjectOperationalTransition(
                project_id=project.project_id,
                from_state=ProjectOperationalState.WAITING_FOR_OWNER,
                to_state=ProjectOperationalState.ACTIVE,
                timestamp=at,
            )
            updated_project = project.model_copy(
                update={"operational_state": ProjectOperationalState.ACTIVE, "updated_at": at}
            )
            self.store.apply_human_action_operational_transition(resolved, updated_project, transition)
        else:
            self.store.save_human_action(resolved)
        return resolved
