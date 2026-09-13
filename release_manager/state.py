from __future__ import annotations

from datetime import datetime

from models.base import ensure_tz
from models.enums import ReleaseStatus
from models.release import Release, ReleaseTarget


_ALLOWED = {
    ReleaseStatus.DRAFT: {ReleaseStatus.PREPARING, ReleaseStatus.WITHDRAWN},
    ReleaseStatus.PREPARING: {ReleaseStatus.READY, ReleaseStatus.FAILED, ReleaseStatus.WITHDRAWN},
    ReleaseStatus.READY: {
        ReleaseStatus.PUBLICATION_REQUIRED,
        ReleaseStatus.PUBLISHED,
        ReleaseStatus.FAILED,
        ReleaseStatus.WITHDRAWN,
    },
    ReleaseStatus.PUBLICATION_REQUIRED: {
        ReleaseStatus.PUBLISHED,
        ReleaseStatus.FAILED,
        ReleaseStatus.WITHDRAWN,
    },
    ReleaseStatus.PUBLISHED: {ReleaseStatus.SUPERSEDED},
    ReleaseStatus.FAILED: {ReleaseStatus.PREPARING, ReleaseStatus.WITHDRAWN},
    ReleaseStatus.WITHDRAWN: set(),
    ReleaseStatus.SUPERSEDED: set(),
}


def _validate(current: ReleaseStatus, target: ReleaseStatus) -> None:
    if target not in _ALLOWED[current]:
        raise ValueError(f"invalid release transition: {current} -> {target}")


def transition_release(value: Release, to_status: ReleaseStatus, at: datetime) -> Release:
    at = ensure_tz(at)
    _validate(value.status, to_status)
    updates = {"status": to_status, "updated_at": at}
    if to_status == ReleaseStatus.PUBLISHED:
        updates["published_at"] = at
    return value.model_copy(update=updates)


def transition_target(value: ReleaseTarget, to_status: ReleaseStatus, at: datetime) -> ReleaseTarget:
    at = ensure_tz(at)
    _validate(value.status, to_status)
    updates = {"status": to_status, "updated_at": at}
    if to_status == ReleaseStatus.PUBLISHED:
        updates["published_at"] = at
    return value.model_copy(update=updates)
