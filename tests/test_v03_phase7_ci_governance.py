from pathlib import Path


def test_core_validation_is_pr_gate_on_current_action_runtime():
    workflow = Path(".github/workflows/core-validation.yml").read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "branches: [main]" in workflow
    assert "name: Core Validation" in workflow
    assert "actions/checkout@v7" in workflow
    assert "actions/setup-python@v7" in workflow
    assert "actions/checkout@v4" not in workflow
    assert "actions/setup-python@v5" not in workflow


def test_legacy_manual_validation_uses_current_action_runtime():
    workflow = Path(".github/workflows/phase3-validation.yml").read_text(encoding="utf-8")
    assert "actions/checkout@v7" in workflow
    assert "actions/setup-python@v7" in workflow
