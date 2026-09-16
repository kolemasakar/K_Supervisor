from __future__ import annotations

from models.base import ensure_tz
from models.enums import ProjectLifecycleState, ProjectSpecStatus, ReleaseStatus
from models.release import Release

from .contracts import ReleaseEvidence, ReleasePreparationOutcome
from .errors import ReleaseManagerError, ReleaseNotReadyError, ReleaseProfileValidationError
from .events import ReleaseEventEmitter
from .publication import PublicationHandoff
from .operational_evidence import OperationalReleaseEvidenceProvider
from .readiness import GenericReleaseReadinessChecker
from .state import transition_release
from .target_preparation import TargetPreparer


class ReleaseManager:
    def __init__(
        self,
        store,
        projects,
        repository_adapter,
        human,
        *,
        notification_broker=None,
        readiness_checker=None,
        operational_evidence_provider=None,
    ):
        self.store = store
        self.projects = projects
        self.repository_adapter = repository_adapter
        self.readiness = readiness_checker or GenericReleaseReadinessChecker()
        self.operational_evidence = (
            operational_evidence_provider
            or OperationalReleaseEvidenceProvider(store, projects)
        )
        self.targets = TargetPreparer(store, repository_adapter, self.readiness)
        self.publication = PublicationHandoff(store, human)
        self.events = ReleaseEventEmitter(store, notification_broker)

    def handle_first_working(
        self,
        project_id,
        version,
        repository,
        at,
        *,
        satisfied_criteria=(),
    ):
        at = ensure_tz(at)
        project = self._project(project_id)
        spec = self._active_spec(project)
        allowed = {
            ProjectLifecycleState.FIRST_WORKING,
            ProjectLifecycleState.RELEASE_PREPARATION,
            ProjectLifecycleState.RELEASE_READY,
        }
        if project.lifecycle_state not in allowed:
            raise ReleaseManagerError(
                f"project must be FIRST_WORKING or a release state: {project.lifecycle_state}"
            )

        criteria = self._readiness_criteria(project_id, satisfied_criteria)
        target_names = self._target_names(spec)
        release_id = f"RELEASE_{project_id}_{version}"
        release = self.store.get_release(release_id)
        created = release is None
        if release is None:
            release = Release(
                release_id=release_id,
                project_id=project_id,
                version=version,
                targets=target_names,
                readiness_criteria=tuple(
                    str(item) for item in spec.release.get("release_readiness_criteria", ())
                ),
                owner_publication_required=True,
                created_at=at,
                updated_at=at,
            )
            self.store.save_release(release)

        if created and project.lifecycle_state == ProjectLifecycleState.FIRST_WORKING:
            self.events.first_working(release, spec)
        if project.lifecycle_state == ProjectLifecycleState.FIRST_WORKING:
            project = self.projects.transition_lifecycle(
                project_id,
                ProjectLifecycleState.RELEASE_PREPARATION,
                "release preparation started after FIRST_WORKING",
                "RELEASE_MANAGER",
                at,
            )

        if release.status in {
            ReleaseStatus.READY,
            ReleaseStatus.PUBLICATION_REQUIRED,
            ReleaseStatus.PUBLISHED,
        }:
            targets = self._release_targets(release)
            reports = self._reports(project, spec, release, targets, repository, criteria)
            return ReleasePreparationOutcome(release, targets, reports)

        if release.status in {ReleaseStatus.DRAFT, ReleaseStatus.FAILED}:
            release = transition_release(release, ReleaseStatus.PREPARING, at)
            self.store.save_release(release)

        reports = []
        ready_targets = []
        try:
            for target_name in target_names:
                target, report = self.targets.prepare(
                    project,
                    spec,
                    release,
                    target_name,
                    repository,
                    at,
                    criteria,
                )
                ready_targets.append(target)
                reports.append(report)
        except (ReleaseNotReadyError, ReleaseProfileValidationError):
            if release.status == ReleaseStatus.PREPARING:
                release = transition_release(release, ReleaseStatus.FAILED, at)
                self.store.save_release(release)
            raise

        release = transition_release(release, ReleaseStatus.READY, at)
        self.store.save_release(release)
        current = self._project(project_id)
        if current.lifecycle_state == ProjectLifecycleState.RELEASE_PREPARATION:
            self.projects.transition_lifecycle(
                project_id,
                ProjectLifecycleState.RELEASE_READY,
                "all release targets passed automated readiness checks",
                "RELEASE_MANAGER",
                at,
            )

        handed_off = tuple(self.publication.open(target, at) for target in ready_targets)
        if any(target.status == ReleaseStatus.PUBLICATION_REQUIRED for target in handed_off):
            release = transition_release(release, ReleaseStatus.PUBLICATION_REQUIRED, at)
            self.store.save_release(release)
        action_id = next((item.human_action_id for item in handed_off if item.human_action_id), None)
        self.events.release_ready(release, spec, action_id)
        return ReleasePreparationOutcome(release, handed_off, tuple(reports))

    def confirm_publication(self, release_id, target_type, at):
        at = ensure_tz(at)
        release = self.store.get_release(release_id)
        if release is None:
            raise KeyError(release_id)
        targets = list(self._release_targets(release))
        selected = next(
            (item for item in targets if item.target_type.upper() == target_type.upper()),
            None,
        )
        if selected is None:
            raise KeyError(target_type)
        published = self.publication.confirm(selected, at)
        targets = [published if item.release_target_id == published.release_target_id else item for item in targets]
        if all(item.status == ReleaseStatus.PUBLISHED for item in targets):
            if release.status in {ReleaseStatus.READY, ReleaseStatus.PUBLICATION_REQUIRED}:
                release = transition_release(release, ReleaseStatus.PUBLISHED, at)
                self.store.save_release(release)
        return ReleasePreparationOutcome(release, tuple(targets), ())

    def _readiness_criteria(self, project_id, explicit):
        operational = self.operational_evidence.collect(project_id)
        return tuple(dict.fromkeys((*tuple(explicit), *operational)))

    def _reports(self, project, spec, release, targets, repository, criteria):
        evidence = ReleaseEvidence(
            available_files=self.repository_adapter.list_files(repository),
            satisfied_criteria=tuple(criteria),
        )
        return tuple(
            self.readiness.check(project, spec, release, target, evidence)
            for target in targets
        )

    def _release_targets(self, release):
        return tuple(
            item
            for item in self.store.list_release_targets(release.project_id)
            if item.release_id == release.release_id
        )

    def _project(self, project_id):
        project = self.projects.get(project_id)
        if project is None:
            raise KeyError(project_id)
        return project

    def _active_spec(self, project):
        if not project.active_project_spec_id:
            raise ReleaseManagerError("project has no active ProjectSpec")
        spec = self.store.get_project_spec(project.active_project_spec_id)
        if spec is None or spec.status != ProjectSpecStatus.APPROVED:
            raise ReleaseManagerError("active ProjectSpec is missing or not APPROVED")
        return spec

    @staticmethod
    def _target_names(spec):
        values = spec.release.get("release_targets", spec.release.get("targets", ()))
        result = tuple(dict.fromkeys(str(item).upper() for item in values if str(item).strip()))
        if not result:
            raise ReleaseManagerError("ProjectSpec declares no release targets")
        return result
