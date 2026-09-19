from __future__ import annotations

from datetime import datetime, timezone

from models.agent import AgentDescriptor, AgentRunResult, CapabilityRef
from models.capability import CapabilityDescriptor
from models.enums import ExecutionStatus, ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from policy.approval import PolicyApprovalBroker
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry
from service_api import ServiceApiV1, ServicePrincipal
from supervisor.dispatch import LocalAgentDispatcher
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.kernel import SupervisorKernel
from workflows import HumanInterventionApprovalRequester, WorkflowEngine

NOW = datetime(2026, 9, 19, 12, 30, tzinfo=timezone.utc)


def onboarding(*, name="Phase Two API", secret_ref=None):
    repository = {
        "repository_provider": "FILESYSTEM",
        "repository_name": "phase-two-api",
        "repository_visibility": "PRIVATE",
    }
    if secret_ref is not None:
        repository["token"] = secret_ref
    return {
        "name": name,
        "short_name": "phase-two-api",
        "purpose": "Operate the control plane through Service/API v1.",
        "problem_statement": "Owner operations need one governed service boundary.",
        "project_type": "AI",
        "success_criteria": ["operator API works"],
        "first_working_criteria": ["governed execution works"],
        "repository": repository,
        "architecture": {"architecture_style": "MODULAR"},
        "notifications": {"primary_channel": "EMAIL"},
    }


def principal(*scopes):
    return ServicePrincipal(principal_id="owner-api", scopes=frozenset(scopes))


def build_operator_stack(path, *, project_id="P2", register_project=True):
    store = SQLitePersistenceStore(path)
    store.initialize()
    projects = ProjectRegistry(store)
    if register_project and projects.get(project_id) is None:
        projects.register(
            Project(
                project_id=project_id,
                name=project_id,
                lifecycle_state=ProjectLifecycleState.BUILDING,
                operational_state=ProjectOperationalState.ACTIVE,
                created_at=NOW,
                updated_at=NOW,
            )
        )

    capabilities = CapabilityRegistry()
    capabilities.register(
        CapabilityDescriptor(
            capability_id="analysis.test",
            capability_version="1.0.0",
            description="Deterministic Phase 2 test capability.",
            operations=("run",),
            input_schema="schema://phase2/input",
            output_schema="schema://phase2/output",
        )
    )
    agents = AgentRegistry(capabilities)
    agents.register(
        AgentDescriptor(
            agent_id="agent.phase2",
            agent_type="TEST",
            agent_version="1.0.0",
            display_name="Phase 2 Agent",
            capabilities=(
                CapabilityRef(
                    capability_id="analysis.test",
                    capability_version="1.0.0",
                ),
            ),
            status="AVAILABLE",
        )
    )
    dispatcher = LocalAgentDispatcher()

    def handler(request):
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
            output={"ok": True, "echo": request.input.get("value")},
        )

    dispatcher.register("agent.phase2", handler)
    kernel = SupervisorKernel(projects, agents, store, dispatcher)
    human = HumanInterventionBroker(store, projects)
    approvals = PolicyApprovalBroker(store, agents, human)
    workflows = WorkflowEngine(
        kernel,
        store,
        HumanInterventionApprovalRequester(human),
    )
    api = ServiceApiV1(
        projects,
        store,
        kernel=kernel,
        workflows=workflows,
        human=human,
        approvals=approvals,
    )
    return store, projects, agents, kernel, workflows, human, approvals, api
