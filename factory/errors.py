class ProjectFactoryError(RuntimeError):
    pass


class BootstrapValidationError(ProjectFactoryError):
    pass


class RepositoryConflictError(ProjectFactoryError):
    pass


class RepositoryUnavailableError(ProjectFactoryError):
    pass


class BootstrapBlockedError(ProjectFactoryError):
    def __init__(self, message: str, human_action_id: str | None = None):
        super().__init__(message)
        self.human_action_id = human_action_id


class GitHubRepositoryError(RepositoryUnavailableError):
    """Safe normalized GitHub repository/provider failure."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        category: str,
        retryable: bool = False,
        status_code: int | None = None,
        retry_after_seconds: int | None = None,
        rate_limit_reset: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.category = category
        self.retryable = retryable
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds
        self.rate_limit_reset = rate_limit_reset

    def __str__(self) -> str:
        return self.message
