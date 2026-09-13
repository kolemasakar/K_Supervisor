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
