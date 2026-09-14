from models.enums import ProjectLifecycleState, ProjectOperationalState
from tests.phase12_support import build_reference_stack
from tests.phase15_support import NOW


def test_project_transitions_emit_audit_events(tmp_path):
    store, _, _, _, _, _, kernel = build_reference_stack(tmp_path)
    kernel.projects.transition_lifecycle(
        "P12", ProjectLifecycleState.VALIDATING, "phase 15 validation", "TEST", NOW
    )
    kernel.projects.transition_operational("P12", ProjectOperationalState.PAUSED, NOW)
    types = [item.event_type for item in store.list_audit_events("P12")]
    assert "PROJECT_LIFECYCLE_TRANSITION" in types
    assert "PROJECT_OPERATIONAL_TRANSITION" in types
