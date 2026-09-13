from datetime import datetime, timezone

from models.agent import AgentDescriptor, CapabilityRef
from models.capability import CapabilityDescriptor, CapabilityRequirement
from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from policy.approval import PolicyApprovalBroker
from policy.dispatcher import PolicyEnforcedDispatcher
from policy.engine import PolicyEngine
from policy.persistence import PersistencePolicyAuditSink
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry
from supervisor.dispatch import LocalAgentDispatcher
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.kernel import SupervisorKernel
from tests.phase5_support import success
from tests.phase6_support import make_spec

NOW = datetime(2026, 9, 13, 19, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 13, 19, 5, tzinfo=timezone.utc)


def build_policy_stack(tmp_path, *, side_effects=("NONE",), risk_class="LOW", policy=None):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()
    projects = ProjectRegistry(store)
    spec = make_spec(project_id="P11", spec_id="PS11").model_copy(
        update={"autonomy": {"policy": policy or {}}}
    )
    project = Project(
        project_id="P11",
        name="Policy Demo",
        active_project_spec_id=spec.project_spec_id,
        lifecycle_state=ProjectLifecycleState.BUILDING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )
    projects.register(project, spec)

    capabilities = CapabilityRegistry()
    capabilities.register(
        CapabilityDescriptor(
            capability_id="policy.test",
            capability_version="1.0.0",
            description="policy test capability",
            operations=("run",),
            input_schema="schema://input",
            output_schema="schema://output",
            side_effects=side_effects,
            risk_class=risk_class,
        )
    )
    agents = AgentRegistry(capabilities)
    agents.register(
        AgentDescriptor(
            agent_id="agent.policy",
            agent_type="TEST",
            agent_version="1.0.0",
            display_name="Policy Agent",
            capabilities=(CapabilityRef(capability_id="policy.test", capability_version="1.0.0"),),
            status="AVAILABLE",
        )
    )

    delegate = LocalAgentDispatcher()
    human = HumanInterventionBroker(store, projects)
    approval = PolicyApprovalBroker(store, agents, human)
    engine = PolicyEngine(
        projects,
        agents,
        approvals=approval,
        audit=PersistencePolicyAuditSink(store),
    )
    dispatcher = PolicyEnforcedDispatcher(engine, delegate, approval)
    kernel = SupervisorKernel(projects, agents, store, dispatcher)
    requirement = CapabilityRequirement(
        capability_id="policy.test",
        version_constraint="1.0.0",
        operation="run",
    )
    return store, projects, agents, delegate, approval, engine, kernel, requirement


def register_success(delegate, calls):
    def handler(request):
        calls.append(request)
        return success(request)

    delegate.register("agent.policy", handler)
