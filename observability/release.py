from datetime import datetime, timezone
from .release_validation import record_release_validation


class ObservableReleaseReadinessChecker:
    def __init__(self, store, checker):
        self.store = store
        self.checker = checker

    def check(self, project, spec, release, target, evidence):
        report = self.checker.check(project, spec, release, target, evidence)
        record_release_validation(
            self.store,
            report=report,
            release_target_id=target.release_target_id,
            created_at=datetime.now(timezone.utc),
        )
        return report
