from __future__ import annotations

from models.project import ProjectSpec

from .contracts import BootstrapFile, RepositoryTarget
from .errors import BootstrapValidationError


BASELINE_DOCUMENTS = {
    "README.md",
    "docs/VISION.md",
    "docs/ARCHITECTURE.md",
    "docs/ROADMAP.md",
}


def validate_bootstrap(
    spec: ProjectSpec,
    target: RepositoryTarget,
    files: tuple[BootstrapFile, ...],
) -> None:
    paths = [item.path for item in files]
    errors: list[str] = []

    if len(paths) != len(set(paths)):
        errors.append("duplicate bootstrap file path")

    missing = sorted(BASELINE_DOCUMENTS.difference(paths))
    if missing:
        errors.append(f"missing baseline documents: {', '.join(missing)}")

    contents = {item.path: item.content for item in files}
    for path in BASELINE_DOCUMENTS:
        if path in contents and not contents[path].strip():
            errors.append(f"empty baseline document: {path}")

    if target.ci_required and ".github/workflows/validation.yml" not in paths:
        errors.append("ci_required repository is missing validation workflow")

    if spec.status.value != "APPROVED":
        errors.append("bootstrap requires APPROVED ProjectSpec")

    if errors:
        raise BootstrapValidationError("; ".join(errors))
