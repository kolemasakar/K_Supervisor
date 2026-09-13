from __future__ import annotations

from models.enums import ReleaseStatus
from models.release import ReleaseTarget

from .contracts import ReleaseEvidence
from .errors import ReleaseNotReadyError, ReleaseProfileValidationError
from .profiles import profile_for
from .state import transition_target


class TargetPreparer:
    def __init__(self, store, repository_adapter, readiness_checker):
        self.store = store
        self.repository_adapter = repository_adapter
        self.readiness = readiness_checker

    def prepare(
        self,
        project,
        spec,
        release,
        target_name,
        repository,
        at,
        satisfied_criteria=(),
    ):
        target_id = f"TARGET_{release.release_id}_{target_name.upper()}"
        target = self.store.get_release_target(target_id)
        if target is None:
            target = ReleaseTarget(
                release_target_id=target_id,
                release_id=release.release_id,
                project_id=release.project_id,
                target_type=target_name.upper(),
                readiness_criteria=release.readiness_criteria,
                owner_publication_required=True,
                created_at=at,
                updated_at=at,
            )
            self.store.save_release_target(target)

        if target.status in {
            ReleaseStatus.READY,
            ReleaseStatus.PUBLICATION_REQUIRED,
            ReleaseStatus.PUBLISHED,
        }:
            return target, self._report(project, spec, release, target, repository, satisfied_criteria)

        if target.status in {ReleaseStatus.DRAFT, ReleaseStatus.FAILED}:
            target = transition_target(target, ReleaseStatus.PREPARING, at)
            self.store.save_release_target(target)

        report = self._report(project, spec, release, target, repository, satisfied_criteria)
        if not report.ready:
            failed = transition_target(target, ReleaseStatus.FAILED, at)
            self.store.save_release_target(failed)
            raise ReleaseNotReadyError(report)

        profile = profile_for(target.target_type)
        generated = profile.generate(spec, release, target)
        self.repository_adapter.apply_files(repository, generated)
        files = self.repository_adapter.list_files(repository)
        missing = profile.validate(files)
        if missing:
            failed = transition_target(target, ReleaseStatus.FAILED, at)
            self.store.save_release_target(failed)
            raise ReleaseProfileValidationError(
                "release profile validation failed: " + ", ".join(missing)
            )

        target = target.model_copy(
            update={
                "artifacts": tuple(item.path for item in generated),
                "checklist": profile.checklist,
            }
        )
        target = transition_target(target, ReleaseStatus.READY, at)
        self.store.save_release_target(target)
        return target, report

    def _report(self, project, spec, release, target, repository, criteria):
        evidence = ReleaseEvidence(
            available_files=self.repository_adapter.list_files(repository),
            satisfied_criteria=tuple(criteria),
        )
        return self.readiness.check(project, spec, release, target, evidence)
