from pathlib import Path

from factory import FilesystemRepositoryAdapter, ProjectFactory
from models.enums import ProjectLifecycleState
from tests.phase6_support import LATER, make_project, make_spec, open_registry


def test_approved_spec_bootstraps_managed_repository(tmp_path):
    store, registry = open_registry(tmp_path / "state.db")
    spec = make_spec()
    registry.register(make_project(spec), spec)

    result = ProjectFactory(
        registry,
        (FilesystemRepositoryAdapter(tmp_path / "repos"),),
    ).bootstrap("P6", LATER)

    project = registry.get("P6")
    repository = Path(result.repository.locator)
    assert project.lifecycle_state == ProjectLifecycleState.BOOTSTRAPPED
    assert project.current_roadmap_phase == "Phase 0"
    assert (repository / ".git").is_dir()
    assert {"README.md", "docs/VISION.md", "docs/ARCHITECTURE.md", "docs/ROADMAP.md"}.issubset(result.files)
    assert ".github/workflows/validation.yml" in result.files
    store.close()
