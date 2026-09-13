from __future__ import annotations

from uuid import uuid4

from models.enums import ReleaseStatus
from models.intervention import HumanActionRequest

from .state import transition_target


class PublicationHandoff:
    def __init__(self, store, human):
        self.store = store
        self.human = human

    def open(self, target, at):
        if not target.owner_publication_required or target.status != ReleaseStatus.READY:
            return target
        action = HumanActionRequest(
            human_action_id=f"HUMAN_RELEASE_{uuid4().hex}",
            project_id=target.project_id,
            action_type="RELEASE_PUBLICATION",
            title=f"Publish {target.target_type} release",
            summary=(
                f"Automated preparation for {target.target_type} is complete. "
                "Publication remains an explicit owner action."
            ),
            required_action=(
                "Review prepared release assets, publish using the owner account, "
                "then confirm publication to K_Supervisor."
            ),
            blocking=True,
            created_at=at,
            resume_condition=f"release_target_published:{target.release_target_id}",
            verification_method="OWNER_PUBLICATION_CONFIRMATION",
        )
        opened = self.human.open(action)
        target = transition_target(target, ReleaseStatus.PUBLICATION_REQUIRED, at)
        target = target.model_copy(update={"human_action_id": opened.human_action_id})
        self.store.save_release_target(target)
        return target

    def confirm(self, target, at):
        if target.status == ReleaseStatus.PUBLISHED:
            return target
        if target.status not in {ReleaseStatus.READY, ReleaseStatus.PUBLICATION_REQUIRED}:
            raise ValueError(f"target is not publishable: {target.status}")
        if target.human_action_id is not None:
            self.human.verify(target.human_action_id, True, at)
        target = transition_target(target, ReleaseStatus.PUBLISHED, at)
        self.store.save_release_target(target)
        return target
