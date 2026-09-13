class ReleaseManagerError(RuntimeError):
    pass


class ReleaseNotReadyError(ReleaseManagerError):
    def __init__(self, report):
        self.report = report
        failed = [item.check_id for item in report.checks if item.required and not item.passed]
        super().__init__("release target is not ready: " + ", ".join(failed))


class ReleaseProfileValidationError(ReleaseManagerError):
    pass
