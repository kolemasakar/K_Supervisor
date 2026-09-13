from datetime import datetime, timezone

from models.agent import AgentDescriptor, AgentRunResult, CapabilityRef
from models.capability import CapabilityDescriptor, CapabilityRequirement
from models.enums import ExecutionStatus, ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry
from supervisor.dispatch import LocalAgentDispatcher
from supervisor.kernel import SupervisorKernel

NOW = datetime(2026, 9, 13, 16, 0, tzinfo=timezone.utc)


def make_project(state=ProjectOperationalState.ACTIVE):
    return Project(project_id="P1", name="P1", lifecycle_state=ProjectLifecycleState.BUILDING,
                   operational_state=state, created_at=NOW, updated_at=NOW)


def make_capability(version="1.0.0"):
    return CapabilityDescriptor(capability_id="analysis.test", capability_version=version,
        description="test", operations=("run",), input_schema="schema://input", output_schema="schema://output")


def make_agent(agent_id, version="1.0.0"):
    return AgentDescriptor(agent_id=agent_id, agent_type="TEST", agent_version="1.0.0",
        display_name=agent_id, capabilities=(CapabilityRef(capability_id="analysis.test", capability_version=version),),
        status="AVAILABLE")


def make_requirement(version="^1.0.0", preferences=None):
    return CapabilityRequirement(capability_id="analysis.test", version_constraint=version,
        operation="run", preferences=preferences or {})


def success(request):
    return AgentRunResult(request_id=request.request_id, project_id=request.project_id,
        task_id=request.task_id, workflow_run_id=request.workflow_run_id, run_id=request.run_id,
        agent_id=request.agent_id, capability_id=request.capability_id,
        capability_version=request.capability_version, status=ExecutionStatus.SUCCEEDED,
        output={"agent_id": request.agent_id})


def build_stack(tmp_path, versions=("1.0.0",), project=None):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()
    projects = ProjectRegistry(store)
    projects.register(project or make_project())
    capabilities = CapabilityRegistry()
    for version in versions:
        capabilities.register(make_capability(version))
    agents = AgentRegistry(capabilities)
    dispatcher = LocalAgentDispatcher()
    kernel = SupervisorKernel(projects, agents, store, dispatcher)
    return store, projects, agents, dispatcher, kernel
