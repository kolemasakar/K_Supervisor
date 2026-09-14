from release_manager import ReleaseManager
from tests.phase13_support import NOW, build_release_stack


def test_release_validation_is_persisted(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    manager = ReleaseManager(store, registry, repos, human)
    outcome = manager.handle_first_working(
        "P13", "1.0.0", repository, NOW,
        satisfied_criteria=("release tests pass",),
    )
    assert outcome.release.status.value == "PUBLICATION_REQUIRED"
    records = store.list_release_validation_records("P13")
    assert records
    assert records[-1].ready
    assert records[-1].release_id == outcome.release.release_id
