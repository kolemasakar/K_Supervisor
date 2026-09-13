from datetime import datetime, timezone

from agent_factory import AgentFactory
from agents import register_reference_agents
from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry
from runtime import AgentRuntimeDispatcher, InProcessRuntimeAdapter
from supervisor.kernel import SupervisorKernel

NOW = datetime(2026, 9, 13, 22, 30, tzinfo=timezone.utc)


def build_reference_stack(tmp_path):
    store = SQLitePersistenceStore(tmp_path / "phase12.db")
    store.initialize()
    projects = ProjectRegistry(store)
    projects.register(
        Project(
            project_id="P12",
            name="Phase 12",
            lifecycle_state=ProjectLifecycleState.BUILDING,
            operational_state=ProjectOperationalState.ACTIVE,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    capabilities = CapabilityRegistry()
    agents = AgentRegistry(capabilities)
    adapter = InProcessRuntimeAdapter()
    factory = AgentFactory(capabilities, agents, adapter)
    builds = register_reference_agents(factory)
    dispatcher = AgentRuntimeDispatcher(agents, adapter)
    kernel = SupervisorKernel(projects, agents, store, dispatcher)
    return store, capabilities, agents, adapter, factory, builds, kernel
