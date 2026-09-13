from __future__ import annotations

from models.project import ProjectSpec

from .contracts import BootstrapFile, RepositoryTarget


def _bullets(values: tuple[str, ...] | list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) or "- None declared."


def generate_bootstrap_files(spec: ProjectSpec, target: RepositoryTarget) -> tuple[BootstrapFile, ...]:
    files = [
        BootstrapFile("README.md", _readme(spec)),
        BootstrapFile("docs/VISION.md", _vision(spec)),
        BootstrapFile("docs/ARCHITECTURE.md", _architecture(spec)),
        BootstrapFile("docs/ROADMAP.md", _roadmap(spec)),
        BootstrapFile(".gitignore", _gitignore()),
        BootstrapFile("src/.gitkeep", ""),
        BootstrapFile("tests/.gitkeep", ""),
        BootstrapFile("agents/.gitkeep", ""),
        BootstrapFile("workflows/.gitkeep", ""),
    ]
    if target.ci_required:
        files.append(BootstrapFile(".github/workflows/validation.yml", _validation_workflow()))
    return tuple(files)


def _readme(spec: ProjectSpec) -> str:
    return f"""# {spec.name}
Автоматично створений базовий опис проєкту під керуванням K_Supervisor.

Status: BOOTSTRAPPED
Project ID: {spec.project_id}
ProjectSpec: {spec.project_spec_id} ({spec.spec_version})

## Purpose

{spec.purpose}

## Problem

{spec.problem_statement}

## First Working Criteria

{_bullets(spec.first_working_criteria)}

## Success Criteria

{_bullets(spec.success_criteria)}

## Governance

This repository was bootstrapped from an approved ProjectSpec. Material scope changes require a new approved ProjectSpec version.
"""


def _vision(spec: ProjectSpec) -> str:
    return f"""# VISION
Базове бачення та критерії успіху проєкту, сформовані з погодженого ProjectSpec.

Version: 0.1
Status: ACTIVE

## Purpose

{spec.purpose}

## Problem Statement

{spec.problem_statement}

## First Working Criteria

{_bullets(spec.first_working_criteria)}

## Success Criteria

{_bullets(spec.success_criteria)}
"""


def _architecture(spec: ProjectSpec) -> str:
    style = spec.architecture.get("architecture_style", "TO_BE_REFINED")
    runtimes = spec.architecture.get("runtime_constraints", [])
    capabilities = spec.agents.get("required_capabilities", [])
    workflows = spec.agents.get("required_workflows", [])
    return f"""# ARCHITECTURE
Початковий архітектурний каркас проєкту, сформований з погоджених обмежень.

Version: 0.1
Status: BASELINE

## Architecture Style

{style}

## Runtime Constraints

{_bullets(list(runtimes))}

## Required Capabilities

{_bullets(list(capabilities))}

## Required Workflows

{_bullets(list(workflows))}

## Boundary

Implementation details may evolve, but material changes must remain compatible with the active ProjectSpec or trigger an amendment.
"""


def _roadmap(spec: ProjectSpec) -> str:
    return f"""# ROADMAP
Початковий план розвитку проєкту від bootstrap до першого робочого стану та перевірки.

Version: 0.1
Status: ACTIVE

## Phase 0 - Bootstrap

- establish repository structure;
- establish baseline documentation;
- establish validation scaffold.

Exit: repository bootstrap validates successfully.

## Phase 1 - First Working

{_bullets(spec.first_working_criteria)}

Exit: all first-working criteria are demonstrated or verified.

## Phase 2 - Validation and Release Readiness

{_bullets(spec.success_criteria)}

Exit: project-specific success criteria required for the selected release target are validated.
"""


def _gitignore() -> str:
    return """__pycache__/
*.py[cod]
.venv/
.env
.env.*
!.env.example
runtime/
logs/
output/
*.log
.DS_Store
Thumbs.db
"""


def _validation_workflow() -> str:
    return """name: Bootstrap Validation

on:
  push:
  pull_request:
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate baseline files
        run: |
          test -f README.md
          test -f docs/VISION.md
          test -f docs/ARCHITECTURE.md
          test -f docs/ROADMAP.md
"""
