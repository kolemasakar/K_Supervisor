from pathlib import Path


def test_core_validation_includes_installed_wheel_phase6_smoke():
    workflow = Path(".github/workflows/core-validation.yml").read_text(encoding="utf-8")
    assert "Installed wheel Phase 6 observability and supply-chain smoke" in workflow
    assert "from observability import (" in workflow
    assert "from tools.sbom import (" in workflow
    assert "from tools.vulnerability_scan import scan" in workflow
    assert 'assert evidence["status"] == "CLEAN"' in workflow


def test_core_validation_enforces_exact_coverage_threshold_separately():
    workflow = Path(".github/workflows/core-validation.yml").read_text(encoding="utf-8")
    assert "python -m coverage report --precision=2 --fail-under=80" in workflow
    assert "--cov-fail-under=80" not in workflow
