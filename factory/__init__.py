from .contracts import BootstrapFile, BootstrapResult, ManagedRepository, RepositoryTarget
from .errors import (
    BootstrapBlockedError,
    BootstrapValidationError,
    ProjectFactoryError,
    GitHubRepositoryError,
    RepositoryConflictError,
    RepositoryUnavailableError,
)
from .onboarding import build_draft_project_spec
from .project_factory import ProjectFactory
from .github_adapter import (
    GovernedGitHubRepositoryAdapter,
    REPOSITORY_AGENT_ID,
    REPOSITORY_CAPABILITY_ID,
    REPOSITORY_CAPABILITY_VERSION,
    register_github_repository_governance,
)
from .github import (
    GITHUB_API_VERSION,
    GitHubHttpResponse,
    GitHubRepositoryResolver,
    GitHubRestClient,
    GitHubTransport,
    GitHubTransportError,
    UrllibGitHubTransport,
)
from .repository import FilesystemRepositoryAdapter, RepositoryAdapter
from .templates import generate_bootstrap_files
from .validator import validate_bootstrap

__all__ = [
    "BootstrapBlockedError",
    "BootstrapFile",
    "BootstrapResult",
    "BootstrapValidationError",
    "FilesystemRepositoryAdapter",
    "GITHUB_API_VERSION",
    "GovernedGitHubRepositoryAdapter",
    "GitHubHttpResponse",
    "GitHubRepositoryError",
    "GitHubRepositoryResolver",
    "GitHubRestClient",
    "GitHubTransport",
    "GitHubTransportError",
    "REPOSITORY_AGENT_ID",
    "REPOSITORY_CAPABILITY_ID",
    "REPOSITORY_CAPABILITY_VERSION",
    "UrllibGitHubTransport",
    "ManagedRepository",
    "ProjectFactory",
    "ProjectFactoryError",
    "RepositoryAdapter",
    "RepositoryConflictError",
    "RepositoryTarget",
    "RepositoryUnavailableError",
    "build_draft_project_spec",
    "generate_bootstrap_files",
    "register_github_repository_governance",
    "validate_bootstrap",
]
