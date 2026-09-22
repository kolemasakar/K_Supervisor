from __future__ import annotations

from uuid import uuid4

from models.enums import ReleaseStatus
from models.intervention import HumanActionRequest
from observability.audit import record_audit

from .state import transition_target


class PublicationHandoff:
    def __init__(self, store, human, *, observability=None):
        self.store = store
        self.human = human
        self.observability = observability

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
        record_audit(
            self.store,
            project_id=target.project_id,
            category="RELEASE",
            event_type="RELEASE_PUBLICATION_REQUIRED",
            occurred_at=at,
            resource_type="ReleaseTarget",
            resource_id=target.release_target_id,
            correlation_id=target.release_id,
            details={"target_type": target.target_type},
        )
        self._observe_publication_required(target)
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
        record_audit(
            self.store,
            project_id=target.project_id,
            category="RELEASE",
            event_type="RELEASE_TARGET_PUBLISHED",
            occurred_at=at,
            resource_type="ReleaseTarget",
            resource_id=target.release_target_id,
            correlation_id=target.release_id,
            details={"target_type": target.target_type},
        )
        return target


    def _observe_publication_required(self, target) -> None:
        if self.observability is None:
            return
        try:
            self.observability.emit(
                project_id=target.project_id,
                event_name="release.publication_required",
                component="release_manager",
                correlation_id=target.release_id,
                status="PUBLICATION_REQUIRED",
                operation="publication_handoff",
                attributes={
                    "target": target.target_type,
                    "operation": "publication_handoff",
                    "result": "required",
                },
            )
        except Exception:
            pass
