from pathlib import Path

import pytest

from factory import FilesystemRepositoryAdapter, ProjectFactory, RepositoryConflictError, RepositoryTarget
from models.enums import ProjectLifecycleState
from tests.phase6_support import LATER, make_project, make_spec, open_registry


def test_existing_conflicting_file_is_not_overwritten(tmp_path):
    store, registry = open_registry(tmp_path / "state.db")
    spec = make_spec()
    registry.register(make_project(spec), spec)
    adapter = FilesystemRepositoryAdapter(tmp_path / "repos")
    repository = adapter.prepare(RepositoryTarget.from_spec(spec))
    readme = Path(repository.locator) / "README.md"
    readme.write_text("owner content\n", encoding="utf-8")

    with pytest.raises(RepositoryConflictError):
        ProjectFactory(registry, (adapter,)).bootstrap("P6", LATER)

    assert readme.read_text(encoding="utf-8") == "owner content\n"
    assert registry.get("P6").lifecycle_state == ProjectLifecycleState.PROVISIONING
    store.close()
