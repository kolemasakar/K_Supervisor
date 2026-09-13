from datetime import datetime, timezone

from models.agent import AgentDescriptor, AgentRunResult, CapabilityRef
from models.capability import CapabilityDescriptor, CapabilityRequirement
from models.enums import ExecutionStatus, ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry
from supervisor.dispatch import LocalAgentDispatcher
from supervisor.kernel import SupervisorKernel
from workflows import WorkflowEngine

NOW = datetime(2026, 9, 13, 17, 0, tzinfo=timezone.utc)


def requirement(capability_id: str) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=capability_id,
        version_constraint="^1.0.0",
        operation="run",
    )


def build_workflow_stack(tmp_path):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()
    projects = ProjectRegistry(store)
    projects.register(
        Project(
            project_id="P1",
            name="P1",
            lifecycle_state=ProjectLifecycleState.BUILDING,
            operational_state=ProjectOperationalState.ACTIVE,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    capabilities = CapabilityRegistry()
    agents = AgentRegistry(capabilities)
    dispatcher = LocalAgentDispatcher()

    for capability_id, agent_id in (("analysis.first", "agent.first"), ("report.second", "agent.second")):
        capabilities.register(
            CapabilityDescriptor(
                capability_id=capability_id,
                capability_version="1.0.0",
                description=capability_id,
                operations=("run",),
                input_schema="schema://input",
                output_schema="schema://output",
            )
        )
        agents.register(
            AgentDescriptor(
                agent_id=agent_id,
                agent_type="TEST",
                agent_version="1.0.0",
                display_name=agent_id,
                capabilities=(CapabilityRef(capability_id=capability_id, capability_version="1.0.0"),),
                status="AVAILABLE",
            )
        )

    def first(request):
        return AgentRunResult(
            request_id=request.request_id,
            project_id=request.project_id,
            task_id=request.task_id,
            workflow_run_id=request.workflow_run_id,
            run_id=request.run_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            status=ExecutionStatus.SUCCEEDED,
            output={"value": request.input.get("seed", 0) + 1},
        )

    def second(request):
        return AgentRunResult(
            request_id=request.request_id,
            project_id=request.project_id,
            task_id=request.task_id,
            workflow_run_id=request.workflow_run_id,
            run_id=request.run_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            status=ExecutionStatus.SUCCEEDED,
            output={"final": request.input.get("value", 0) * 2},
        )

    dispatcher.register("agent.first", first)
    dispatcher.register("agent.second", second)
    kernel = SupervisorKernel(projects, agents, store, dispatcher)
    engine = WorkflowEngine(kernel, store)
    return store, projects, kernel, engine
