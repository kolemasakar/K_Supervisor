import pytest

from factory import BootstrapBlockedError, ProjectFactory
from models.enums import ProjectLifecycleState, ProjectOperationalState
from supervisor.human_intervention import HumanInterventionBroker
from tests.phase6_support import LATER, make_project, make_spec, open_registry


def test_missing_external_adapter_creates_owner_action(tmp_path):
    store, registry = open_registry(tmp_path / "state.db")
    spec = make_spec(provider="GITHUB", provisioning="OWNER_ACTION_REQUIRED")
    registry.register(make_project(spec), spec)
    broker = HumanInterventionBroker(store, registry)

    with pytest.raises(BootstrapBlockedError) as error:
        ProjectFactory(registry, (), broker).bootstrap("P6", LATER)

    project = registry.get("P6")
    assert error.value.human_action_id is not None
    assert project.lifecycle_state == ProjectLifecycleState.PROVISIONING
    assert project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER
    assert len(store.list_human_actions("P6")) == 1
    store.close()
