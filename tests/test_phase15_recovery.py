from persistence import SQLitePersistenceStore
from release_manager import ReleaseManager
from tests.phase13_support import NOW, build_release_stack


def test_observability_records_survive_restart(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    ReleaseManager(store, registry, repos, human).handle_first_working(
        "P13", "1.0.0", repository, NOW,
        satisfied_criteria=("release tests pass",),
    )
    path = store.path
    expected = len(store.list_release_validation_records("P13"))
    store.close()

    with SQLitePersistenceStore(path) as recovered:
        assert len(recovered.list_release_validation_records("P13")) == expected
        assert recovered.list_audit_events("P13")
