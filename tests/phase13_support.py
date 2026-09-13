from datetime import datetime, timezone

from factory.contracts import BootstrapFile, RepositoryTarget
from factory.repository import FilesystemRepositoryAdapter
from models.enums import ProjectLifecycleState, ProjectOperationalState, ProjectSpecStatus
from models.project import Project, ProjectSpec
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry
from supervisor.human_intervention import HumanInterventionBroker

NOW = datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 13, 20, 5, tzinfo=timezone.utc)


def build_release_stack(tmp_path, *, readiness=("release tests pass",)):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()
    registry = ProjectRegistry(store)
    spec = ProjectSpec(
        project_spec_id="PS13",
        project_id="P13",
        spec_version="1.0",
        status=ProjectSpecStatus.APPROVED,
        created_at=NOW,
        updated_at=NOW,
        approved_at=NOW,
        name="Release Demo",
        short_name="release-demo",
        purpose="Validate automated release preparation.",
        problem_statement="Working projects require controlled publication preparation.",
        project_type="AI",
        success_criteria=("release is owner controlled",),
        first_working_criteria=("working path exists",),
        documentation={"required_documents": ["README.md", "ARCHITECTURE.md", "ROADMAP.md"]},
        repository={"repository_provider": "FILESYSTEM"},
        architecture={"architecture_style": "MODULAR"},
        notifications={"primary_channel": "EMAIL"},
        release={
            "release_targets": ["GPT_STORE"],
            "release_readiness_criteria": list(readiness),
            "publication_owner": "OWNER",
        },
    )
    project = Project(
        project_id="P13",
        name="Release Demo",
        active_project_spec_id=spec.project_spec_id,
        lifecycle_state=ProjectLifecycleState.FIRST_WORKING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )
    registry.register(project, spec)
    human = HumanInterventionBroker(store, registry)
    repos = FilesystemRepositoryAdapter(tmp_path / "repos")
    repository = repos.prepare(
        RepositoryTarget(
            provider="FILESYSTEM",
            owner=None,
            name="release-demo",
            visibility="PRIVATE",
            url=None,
            default_branch="main",
            ci_required=True,
            provisioning="AUTOMATABLE",
        )
    )
    repos.apply_files(
        repository,
        tuple(
            BootstrapFile(path, f"# {path}\n")
            for path in ("README.md", "ARCHITECTURE.md", "ROADMAP.md")
        ),
    )
    return store, registry, human, repos, repository
