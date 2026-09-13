import pytest

from models.enums import ReleaseStatus
from models.release import Release, ReleaseTarget
from release_manager import transition_release, transition_target

from tests.phase13_support import LATER, NOW


def test_release_and_target_state_machines_reject_invalid_transitions():
    release = Release(
        release_id="R13",
        project_id="P13",
        version="1.0.0",
        targets=("GPT_STORE",),
        created_at=NOW,
        updated_at=NOW,
    )
    target = ReleaseTarget(
        release_target_id="RT13",
        release_id="R13",
        project_id="P13",
        target_type="GPT_STORE",
        created_at=NOW,
        updated_at=NOW,
    )

    with pytest.raises(ValueError):
        transition_release(release, ReleaseStatus.PUBLISHED, LATER)
    with pytest.raises(ValueError):
        transition_target(target, ReleaseStatus.PUBLISHED, LATER)

    assert transition_release(release, ReleaseStatus.PREPARING, LATER).status == ReleaseStatus.PREPARING
    assert transition_target(target, ReleaseStatus.PREPARING, LATER).status == ReleaseStatus.PREPARING
