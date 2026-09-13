class SchedulerError(RuntimeError):
    pass


class SchedulerClosedError(SchedulerError):
    pass


class DuplicateWorkError(SchedulerError):
    pass


class ProjectBudgetExceeded(SchedulerError):
    pass
