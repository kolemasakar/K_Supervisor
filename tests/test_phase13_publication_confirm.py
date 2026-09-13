from models.enums import ProjectOperationalState, ReleaseStatus
from release_manager import ReleaseManager

from tests.phase13_support import LATER, NOW, build_release_stack


def test_publication_remains_owner_action_until_explicit_confirmation(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    manager = ReleaseManager(store, registry, repos, human)
    prepared = manager.handle_first_working(
        "P13",
        "0.1.0",
        repository,
        NOW,
        satisfied_criteria=("release tests pass",),
    )

    assert prepared.release.status == ReleaseStatus.PUBLICATION_REQUIRED
    assert prepared.targets[0].published_at is None

    published = manager.confirm_publication(
        prepared.release.release_id,
        "GPT_STORE",
        LATER,
    )

    assert published.release.status == ReleaseStatus.PUBLISHED
    assert published.release.published_at == LATER
    assert published.targets[0].status == ReleaseStatus.PUBLISHED
    assert published.targets[0].published_at == LATER
    assert registry.get("P13").operational_state == ProjectOperationalState.ACTIVE
    store.close()
