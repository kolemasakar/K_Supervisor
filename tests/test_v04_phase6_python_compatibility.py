from pathlib import Path
import tomllib


def test_package_metadata_admits_only_qualified_stable_python_minors():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["requires-python"] == ">=3.13,<3.15"


def test_core_validation_declares_both_qualified_python_minors_and_aggregate_gate():
    workflow = Path(".github/workflows/core-validation.yml").read_text(encoding="utf-8")
    assert '- python-version: "3.13"' in workflow
    assert '- python-version: "3.14"' in workflow
    assert 'lock-file: "requirements/ci-py313.lock"' in workflow
    assert 'lock-file: "requirements/ci-py314.lock"' in workflow
    assert 'name: Core Validation' in workflow
    assert 'needs: python-validation' in workflow
    assert 'PYTHON_VALIDATION_RESULT' in workflow
