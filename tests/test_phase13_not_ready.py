import pytest

from models.enums import ProjectLifecycleState, ProjectOperationalState, ReleaseStatus
from release_manager import ReleaseManager, ReleaseNotReadyError

from tests.phase13_support import NOW, build_release_stack


def test_unsatisfied_readiness_criterion_fails_release_without_publication_handoff(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    manager = ReleaseManager(store, registry, repos, human)

    with pytest.raises(ReleaseNotReadyError):
        manager.handle_first_working("P13", "0.1.0", repository, NOW)

    project = registry.get("P13")
    release = store.get_release("RELEASE_P13_0.1.0")
    target = store.get_release_target("TARGET_RELEASE_P13_0.1.0_GPT_STORE")
    assert project.lifecycle_state == ProjectLifecycleState.RELEASE_PREPARATION
    assert project.operational_state == ProjectOperationalState.ACTIVE
    assert release.status == ReleaseStatus.FAILED
    assert target.status == ReleaseStatus.FAILED
    assert not store.list_human_actions("P13")
    store.close()
