import pytest

from access import AccessReference, EnvironmentSecretBackend, environment_key
from models.project import ProjectSpec
from tests.phase6_support import make_spec


def test_environment_secret_backend_keeps_value_redacted():
    reference = AccessReference(uri="secret://project/P1/github")
    key = environment_key(reference)
    backend = EnvironmentSecretBackend({key: "test-value"})

    resolved = backend.resolve(reference)
    assert resolved.reveal() == "test-value"
    assert "test-value" not in str(resolved)
    assert "test-value" not in repr(resolved)
    assert backend.available(reference)


def test_project_spec_rejects_raw_access_data_and_accepts_reference():
    raw = make_spec().model_dump()
    raw["integrations"] = {"api_key": "plain-value"}
    with pytest.raises(ValueError):
        ProjectSpec.model_validate(raw)

    raw["integrations"] = {"api_key": "secret://project/P6/provider"}
    validated = ProjectSpec.model_validate(raw)
    assert validated.integrations["api_key"].startswith("secret://")
