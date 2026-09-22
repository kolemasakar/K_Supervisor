from __future__ import annotations

from datetime import datetime, timezone

from factory.contracts import RepositoryOperationContext
from models.enums import ReleaseStatus
from models.release import ReleaseTarget
from observability.release_validation import record_release_validation

from .contracts import ReleaseEvidence
from .errors import ReleaseNotReadyError, ReleaseProfileValidationError
from .profiles import profile_for
from .state import transition_target


class TargetPreparer:
    def __init__(self, store, repository_adapter, readiness_checker, *, observability=None):
        self.store = store
        self.repository_adapter = repository_adapter
        self.readiness = readiness_checker
        self.observability = observability

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
        target_type = target_name.upper()
        self._observe(
            project_id=project.project_id,
            event_name="release.prepare.started",
            target=target_type,
            operation="prepare",
            release_id=release.release_id,
            status="STARTED",
        )
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

        context = RepositoryOperationContext(
            project_id=project.project_id,
            project_spec_id=spec.project_spec_id,
            idempotency_key=f"release-manager:{release.release_id}:{target_name.lower()}",
        )

        if target.status in {
            ReleaseStatus.READY,
            ReleaseStatus.PUBLICATION_REQUIRED,
            ReleaseStatus.PUBLISHED,
        }:
            return target, self._report(
                project,
                spec,
                release,
                target,
                repository,
                satisfied_criteria,
                context=context,
            )

        if target.status in {ReleaseStatus.DRAFT, ReleaseStatus.FAILED}:
            target = transition_target(target, ReleaseStatus.PREPARING, at)
            self.store.save_release_target(target)

        report = self._report(
            project,
            spec,
            release,
            target,
            repository,
            satisfied_criteria,
            context=context,
        )
        if not report.ready:
            failed = transition_target(target, ReleaseStatus.FAILED, at)
            self.store.save_release_target(failed)
            self._observe(
                project_id=project.project_id,
                event_name="release.prepare.failed",
                target=target.target_type,
                operation="prepare",
                release_id=release.release_id,
                status="FAILED",
                result="failed",
                error_code="RELEASE_NOT_READY",
            )
            raise ReleaseNotReadyError(report)

        profile = profile_for(target.target_type)
        reference_requester = getattr(profile, "reference_requests", None)
        if callable(reference_requester):
            reference_contents = {
                path: self._read_text_file(repository, path, context)
                for path in reference_requester(spec)
            }
            generated = profile.generate(
                spec,
                release,
                target,
                reference_contents=reference_contents,
            )
        else:
            generated = profile.generate(spec, release, target)
        self._apply_files(repository, generated, context)
        files = self._list_files(repository, context)
        missing = tuple(
            dict.fromkeys(
                (
                    *profile.validate(files),
                    *sorted({item.path for item in generated}.difference(files)),
                )
            )
        )
        if missing:
            failed = transition_target(target, ReleaseStatus.FAILED, at)
            self.store.save_release_target(failed)
            self._observe(
                project_id=project.project_id,
                event_name="release.prepare.failed",
                target=target.target_type,
                operation="prepare",
                release_id=release.release_id,
                status="FAILED",
                result="failed",
                error_code="RELEASE_PROFILE_VALIDATION_FAILED",
            )
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
        self._observe(
            project_id=project.project_id,
            event_name="release.prepare.completed",
            target=target.target_type,
            operation="prepare",
            release_id=release.release_id,
            status="READY",
            result="success",
        )
        return target, report

    def _report(
        self,
        project,
        spec,
        release,
        target,
        repository,
        criteria,
        *,
        context: RepositoryOperationContext,
    ):
        evidence = ReleaseEvidence(
            available_files=self._list_files(repository, context),
            satisfied_criteria=tuple(criteria),
        )
        report = self.readiness.check(project, spec, release, target, evidence)
        record_release_validation(
            self.store,
            report=report,
            release_target_id=target.release_target_id,
            created_at=datetime.now(timezone.utc),
        )
        return report


    def _observe(
        self,
        *,
        project_id: str,
        event_name: str,
        target: str,
        operation: str,
        release_id: str,
        status: str,
        result: str | None = None,
        error_code: str | None = None,
    ) -> None:
        if self.observability is None:
            return
        attributes = {"target": target, "operation": operation}
        if result is not None:
            attributes["result"] = result
        if error_code is not None:
            attributes["error_code"] = error_code
        try:
            self.observability.emit(
                project_id=project_id,
                event_name=event_name,
                component="release_manager",
                correlation_id=release_id,
                status=status,
                operation=operation,
                error_code=error_code,
                attributes=attributes,
            )
        except Exception:
            pass

    def _list_files(self, repository, context: RepositoryOperationContext):
        if getattr(self.repository_adapter, "supports_operation_context", False):
            return self.repository_adapter.list_files(repository, context=context)
        return self.repository_adapter.list_files(repository)

    def _apply_files(self, repository, files, context: RepositoryOperationContext) -> None:
        if getattr(self.repository_adapter, "supports_operation_context", False):
            self.repository_adapter.apply_files(repository, files, context=context)
            return
        self.repository_adapter.apply_files(repository, files)

    def _read_text_file(
        self,
        repository,
        path: str,
        context: RepositoryOperationContext,
    ) -> str | None:
        reader = getattr(self.repository_adapter, "read_text_file", None)
        if not callable(reader):
            raise ReleaseProfileValidationError(
                "PLUGIN_REFERENCE_MISSING: repository adapter cannot read reference resources"
            )
        if getattr(self.repository_adapter, "supports_operation_context", False):
            return reader(repository, path, context=context)
        return reader(repository, path)
