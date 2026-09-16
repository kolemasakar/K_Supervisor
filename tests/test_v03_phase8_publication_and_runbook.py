from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "package-publish.yml"
RUNBOOK = ROOT / "docs" / "OPERATIONS_RUNBOOK.md"


def test_package_publication_workflow_is_manual_owner_gated_and_trusted():
    text = WORKFLOW.read_text()
    assert "workflow_dispatch:" in text
    trigger_block = text.split("permissions:", 1)[0]
    assert "push:" not in trigger_block
    assert "pull_request:" not in trigger_block
    assert "release:" not in trigger_block
    assert "schedule:" not in trigger_block
    assert "confirm_owner_publication:" in text
    assert "inputs.confirm_owner_publication == true" in text
    assert "actions/checkout@v7" in text
    assert "actions/setup-python@v7" in text
    assert "actions/upload-artifact@v7" in text
    assert "actions/download-artifact@v7" in text
    assert "python -m build" in text
    assert "python -m twine check dist/*" in text
    assert "name: pypi" in text
    assert "id-token: write" in text
    assert "pypa/gh-action-pypi-publish@release/v1" in text
    assert "PYPI_TOKEN" not in text
    assert "password:" not in text


def test_operations_runbook_covers_required_phase8_procedures():
    text = RUNBOOK.read_text()
    for heading in (
        "## Pre-deployment qualification",
        "## Online backup",
        "## Backup verification",
        "## Upgrade qualification",
        "## Restore",
        "## Rollback",
        "## Project restart and recovery",
        "## Release readiness",
        "## Package-index publication",
        "## Incident and failure handling",
    ):
        assert heading in text
    assert "RELEASE_READY" in text
    assert "WAITING_FOR_OWNER" in text
    assert "Trusted Publishing" in text
    assert "manual-only" in text
