from pathlib import Path


LOCKS = (
    Path("requirements/ci-py313.lock"),
    Path("requirements/ci-py314.lock"),
)


def _entries(path: Path) -> dict[str, str]:
    entries = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assert "==" in line
        name, version = line.split("==", 1)
        assert name and version
        assert not any(token in version for token in ("<", ">", "~", "*", ","))
        entries[name.lower()] = version
    return entries


def test_ci_locks_are_exact_and_cover_runtime_test_and_build_dependencies():
    required = {
        "pip",
        "setuptools",
        "wheel",
        "build",
        "pydantic",
        "pydantic-core",
        "pytest",
        "pytest-cov",
        "coverage",
        "jsonschema",
    }
    for path in LOCKS:
        assert path.exists()
        entries = _entries(path)
        assert required <= set(entries)


def test_python_minor_locks_are_separate_resolution_artifacts():
    py313 = _entries(LOCKS[0])
    py314 = _entries(LOCKS[1])
    assert py313
    assert py314
    assert py313["pydantic-core"] == "2.46.5"
    assert py314["pydantic-core"] == "2.46.5"


def test_core_validation_uses_isolated_lock_driven_builds():
    workflow = Path(".github/workflows/core-validation.yml").read_text(encoding="utf-8")
    assert 'lock-file: "requirements/ci-py313.lock"' in workflow
    assert 'lock-file: "requirements/ci-py314.lock"' in workflow
    assert "python -m venv .venv-ci" in workflow
    assert "--only-binary=:all:" in workflow
    assert 'pip==26.2.1' in workflow
    assert "python -m build --wheel --no-isolation" in workflow
