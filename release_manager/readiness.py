from __future__ import annotations

from models.enums import ProjectLifecycleState

from .contracts import ReleaseCheckResult, ReleaseEvidence, ReleaseReadinessReport


_READY_STATES = {
    ProjectLifecycleState.FIRST_WORKING,
    ProjectLifecycleState.RELEASE_PREPARATION,
    ProjectLifecycleState.RELEASE_READY,
}


class GenericReleaseReadinessChecker:
    def check(self, project, spec, release, target, evidence: ReleaseEvidence):
        files = set(evidence.available_files)
        satisfied = set(evidence.satisfied_criteria)
        declared = spec.release.get("release_targets", spec.release.get("targets", release.targets))
        declared = {str(item).upper() for item in declared}
        required_docs = spec.documentation.get(
            "required_documents", ("README.md", "ARCHITECTURE.md", "ROADMAP.md")
        )
        criteria = list(release.readiness_criteria)
        criteria.extend(str(item) for item in spec.release.get("release_readiness_criteria", ()))

        checks = [
            ReleaseCheckResult(
                check_id="project_first_working",
                passed=project.lifecycle_state in _READY_STATES,
                summary="Project reached the release lifecycle gate.",
            ),
            ReleaseCheckResult(
                check_id="target_declared",
                passed=target.target_type.upper() in declared,
                summary=f"Target is declared: {target.target_type}",
            ),
        ]
        checks.extend(
            ReleaseCheckResult(
                check_id=f"document:{path}",
                passed=str(path) in files,
                summary=f"Required document is present: {path}",
            )
            for path in required_docs
        )
        checks.extend(
            ReleaseCheckResult(
                check_id=f"criterion:{criterion}",
                passed=criterion in satisfied,
                summary=f"Readiness criterion is satisfied: {criterion}",
            )
            for criterion in dict.fromkeys(criteria)
        )
        return ReleaseReadinessReport(
            release_id=release.release_id,
            project_id=release.project_id,
            target_type=target.target_type,
            checks=tuple(checks),
        )
