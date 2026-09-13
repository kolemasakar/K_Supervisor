from models.enums import ProjectLifecycleState, ProjectOperationalState, ReleaseStatus
from release_manager import ReleaseManager

from tests.phase13_support import NOW, build_release_stack


def test_first_working_prepares_gpt_store_release_and_owner_handoff(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    manager = ReleaseManager(store, registry, repos, human)

    outcome = manager.handle_first_working(
        "P13",
        "0.1.0",
        repository,
        NOW,
        satisfied_criteria=("release tests pass",),
    )

    project = registry.get("P13")
    assert project.lifecycle_state == ProjectLifecycleState.RELEASE_READY
    assert project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER
    assert outcome.release.status == ReleaseStatus.PUBLICATION_REQUIRED
    assert outcome.targets[0].status == ReleaseStatus.PUBLICATION_REQUIRED
    assert outcome.targets[0].human_action_id is not None

    files = set(repos.list_files(repository))
    assert "release/gpt_store/GPT_STORE_PROFILE.json" in files
    assert "release/gpt_store/GPT_INSTRUCTIONS.md" in files
    assert "release/gpt_store/GPT_STORE_LISTING.md" in files
    assert "release/gpt_store/GPT_PUBLICATION_CHECKLIST.md" in files

    event_types = {item.event_type for item in store.list_notifications("P13")}
    assert {"FIRST_WORKING_REACHED", "RELEASE_READY"}.issubset(event_types)
    assert registry.recover("P13").release_targets[0].release_target_id == outcome.targets[0].release_target_id
    store.close()
