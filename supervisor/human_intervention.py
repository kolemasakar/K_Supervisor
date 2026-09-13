from datetime import datetime

from models.enums import HumanActionStatus, ProjectOperationalState
from models.intervention import HumanActionRequest
from persistence.base import PersistenceStore
from registry.project_registry import ProjectRegistry


class HumanInterventionBroker:
    def __init__(self, store: PersistenceStore, registry: ProjectRegistry):
        self.store = store
        self.registry = registry

    def open(self, action: HumanActionRequest) -> HumanActionRequest:
        if self.registry.get(action.project_id) is None:
            raise KeyError(action.project_id)
        state = HumanActionStatus.WAITING_FOR_OWNER if action.blocking else HumanActionStatus.OPEN
        saved = action.model_copy(update={"status": state})
        self.store.save_human_action(saved)
        if action.blocking:
            project = self.registry.get(action.project_id)
            if project.operational_state != ProjectOperationalState.WAITING_FOR_OWNER:
                self.registry.transition_operational(
                    action.project_id,
                    ProjectOperationalState.WAITING_FOR_OWNER,
                    action.created_at,
                )
        return saved

    def verify(self, human_action_id: str, ok: bool, at: datetime) -> HumanActionRequest:
        action = self.store.get_human_action(human_action_id)
        if action is None:
            raise KeyError(human_action_id)
        if not ok:
            return action
        resolved = action.model_copy(
            update={"status": HumanActionStatus.VERIFIED, "resolved_at": at}
        )
        self.store.save_human_action(resolved)
        blockers = [
            item
            for item in self.store.list_human_actions(action.project_id)
            if item.human_action_id != human_action_id
            and item.blocking
            and item.status not in {HumanActionStatus.VERIFIED, HumanActionStatus.CANCELLED}
        ]
        project = self.registry.get(action.project_id)
        if action.blocking and not blockers and project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER:
            self.registry.transition_operational(
                action.project_id,
                ProjectOperationalState.ACTIVE,
                at,
            )
        return resolved
