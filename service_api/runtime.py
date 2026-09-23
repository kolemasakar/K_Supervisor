from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from access import EnvironmentSecretBackend, SecretBackend
from agents import ModelBackedAgent
from factory import FilesystemRepositoryAdapter, ProjectFactory
from factory.governed_github import build_governed_github_repository_adapter
from factory.repository import RoutedRepositoryAdapter
from integrations.gateway import SideEffectGateway
from models.agent import AgentDescriptor, CapabilityRef
from models.capability import CapabilityDescriptor
from observability import (
    DeploymentQualifier,
    ProductionMetricRegistry,
    ProductionObservability,
    ServiceHealthEvaluator,
    TelemetryRecorder,
)
from persistence import SQLitePersistenceStore
from policy.approval import PolicyApprovalBroker
from policy.engine import PolicyEngine
from policy.persistence import PersistencePolicyAuditSink
from providers import (
    ModelProfile,
    OpenAIResponsesProvider,
    PriorityModelSelector,
)
from registry import (
    AgentRegistry,
    CapabilityRegistry,
    ProjectRegistry,
    ProviderRegistry,
)
from release_manager import ReleaseManager
from runtime.contracts import ExecutionControl, RuntimeLimits
from supervisor.dispatch import LocalAgentDispatcher
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.kernel import SupervisorKernel
from workflows import HumanInterventionApprovalRequester, WorkflowEngine

from .auth import StaticBearerAuthenticator
from .contracts import ServicePrincipal
from .service import ServiceApiV1
from .wsgi import WsgiServiceAppV1


MODEL_CAPABILITY_ID = "generation.model"
MODEL_CAPABILITY_VERSION = "1.0.0"
MODEL_AGENT_ID = "agent.model.production"


@dataclass
class ServiceRuntime:
    """Production composition root for the single-node Service/API process."""

    config: object
    store: SQLitePersistenceStore
    projects: ProjectRegistry
    capabilities: CapabilityRegistry
    agents: AgentRegistry
    dispatcher: LocalAgentDispatcher
    kernel: SupervisorKernel
    human: HumanInterventionBroker
    approvals: PolicyApprovalBroker
    workflows: WorkflowEngine
    releases: ReleaseManager
    telemetry: TelemetryRecorder
    production_metrics: ProductionMetricRegistry
    production_observability: ProductionObservability
    health: ServiceHealthEvaluator
    qualifier: DeploymentQualifier
    authenticator: StaticBearerAuthenticator
    api: ServiceApiV1
    app: WsgiServiceAppV1
    project_factory: ProjectFactory | None = None
    _closed: bool = field(default=False, init=False, repr=False)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.store.close()


def _configure_model_provider(
    config,
    *,
    backend: SecretBackend,
    store,
    projects,
    capabilities,
    agents,
    approvals,
    dispatcher,
    observability,
    transport=None,
) -> None:
    provider_config = config.model_provider
    if provider_config is None or not provider_config.enabled:
        return
    credential_ref = provider_config.credential_ref
    if credential_ref is None:
        raise ValueError("enabled model_provider requires credential_ref")

    capability = CapabilityDescriptor(
        capability_id=MODEL_CAPABILITY_ID,
        capability_version=MODEL_CAPABILITY_VERSION,
        description="Generate text through the governed production MODEL provider.",
        operations=("run",),
        input_schema="schema://model/generation/input",
        output_schema="schema://model/generation/output",
        side_effects=("WRITE_EXTERNAL",),
        risk_class="LOW",
        metadata={"reference": False, "model_backed": True},
    )
    capabilities.register(capability)
    agents.register(
        AgentDescriptor(
            agent_id=MODEL_AGENT_ID,
            agent_type="MODEL_BACKED",
            agent_version="1.0.0",
            display_name="Governed Model Agent",
            capabilities=(
                CapabilityRef(
                    capability_id=MODEL_CAPABILITY_ID,
                    capability_version=MODEL_CAPABILITY_VERSION,
                ),
            ),
            status="AVAILABLE",
            metadata={"reference": False},
        )
    )

    providers = ProviderRegistry()
    providers.register(
        OpenAIResponsesProvider(
            secret_backend=backend,
            credential_ref=credential_ref,
            models=tuple(
                ModelProfile(
                    model_id=item.model_id,
                    features=item.features,
                    context_window=item.context_window,
                    priority=item.priority,
                )
                for item in provider_config.models
            ),
            default_model=provider_config.default_model,
            transport=transport,
            connect_timeout_seconds=provider_config.connect_timeout_seconds,
            request_timeout_seconds=provider_config.request_timeout_seconds,
            max_retries=provider_config.max_retries,
            retry_backoff_seconds=provider_config.retry_backoff_seconds,
            default_max_output_tokens=provider_config.default_max_output_tokens,
            max_output_tokens_limit=provider_config.max_output_tokens_limit,
        )
    )
    policy = PolicyEngine(
        projects,
        agents,
        approvals=approvals,
        audit=PersistencePolicyAuditSink(store),
    )
    gateway = SideEffectGateway(
        store,
        policy,
        providers=providers,
        observability=observability,
    )
    model_agent = ModelBackedAgent(
        gateway,
        PriorityModelSelector(),
        provider_access_refs={provider_config.provider_id: (credential_ref,)},
    )

    def handle(request):
        control = ExecutionControl(RuntimeLimits.from_request(dict(request.limits)))
        return model_agent(request, control)

    dispatcher.register(MODEL_AGENT_ID, handle)


def build_service_runtime(
    config,
    *,
    secret_backend: SecretBackend | None = None,
    model_transport=None,
    github_transport=None,
) -> ServiceRuntime:
    host = config.service_host
    if host is None:
        raise ValueError("service_host configuration is required for serve")
    if not host.principals:
        raise ValueError("service_host requires at least one authenticated principal")

    store = SQLitePersistenceStore(config.state_db_path)
    try:
        store.initialize()
        backend = secret_backend or EnvironmentSecretBackend()
        projects = ProjectRegistry(store)
        capabilities = CapabilityRegistry()
        agents = AgentRegistry(capabilities)
        dispatcher = LocalAgentDispatcher()
        human = HumanInterventionBroker(store, projects)
        approvals = PolicyApprovalBroker(store, agents, human)

        telemetry = TelemetryRecorder(store)
        production_metrics = ProductionMetricRegistry()
        production_observability = ProductionObservability(
            telemetry=telemetry,
            metrics=production_metrics,
        )

        _configure_model_provider(
            config,
            backend=backend,
            store=store,
            projects=projects,
            capabilities=capabilities,
            agents=agents,
            approvals=approvals,
            dispatcher=dispatcher,
            observability=production_observability,
            transport=model_transport,
        )

        kernel = SupervisorKernel(projects, agents, store, dispatcher)
        workflows = WorkflowEngine(
            kernel,
            store,
            HumanInterventionApprovalRequester(human),
        )
        health = ServiceHealthEvaluator(
            {
                "persistence": (
                    lambda: store.is_initialized
                    and store.schema_version == SQLitePersistenceStore.SCHEMA_VERSION,
                    True,
                )
            }
        )
        qualifier = DeploymentQualifier(store, projects, health)

        if host.extensions:
            from ksupervisor.extensions import (
                ExtensionContext,
                ExtensionGovernance,
                activate_extension,
            )

            context = ExtensionContext({
                "store": store,
                "projects": projects,
                "capabilities": capabilities,
                "agents": agents,
                "dispatcher": dispatcher,
                "kernel": kernel,
                "human": human,
                "approvals": approvals,
                "workflows": workflows,
                "telemetry": telemetry,
                "production_metrics": production_metrics,
                "production_observability": production_observability,
            })
            governance = ExtensionGovernance(store)
            for extension in host.extensions:
                try:
                    activate_extension(
                        extension.kind,
                        extension.name,
                        context,
                        governance,
                    )
                except Exception:
                    if config.strict_extensions:
                        raise

        repository_root = Path(config.state_db_path).resolve().parent / "repositories"
        filesystem_repository = FilesystemRepositoryAdapter(repository_root)
        github_repository = build_governed_github_repository_adapter(
            store,
            projects,
            human,
            backend,
            transport=github_transport,
            observability=production_observability,
        )
        repository_adapters = (
            filesystem_repository,
            github_repository,
        )
        project_factory = ProjectFactory(
            projects,
            repository_adapters,
            human,
        )
        routed_repository = RoutedRepositoryAdapter(repository_adapters)
        releases = ReleaseManager(
            store,
            projects,
            routed_repository,
            human,
            observability=production_observability,
        )

        tokens: dict[str, ServicePrincipal] = {}
        principal_ids: set[str] = set()
        for item in host.principals:
            if item.principal_id in principal_ids:
                raise ValueError("service principal_id values must be unique")
            principal_ids.add(item.principal_id)
            token = backend.resolve(item.token_ref).reveal()
            if not token:
                raise ValueError("resolved service bearer token must not be empty")
            if token in tokens:
                raise ValueError("service bearer tokens must be unique")
            tokens[token] = ServicePrincipal(
                principal_id=item.principal_id,
                scopes=frozenset(item.scopes),
            )

        authenticator = StaticBearerAuthenticator(tokens)
        api = ServiceApiV1(
            projects,
            store,
            telemetry,
            observability=production_observability,
            kernel=kernel,
            workflows=workflows,
            human=human,
            approvals=approvals,
            releases=releases,
            project_factory=project_factory,
        )
        app = WsgiServiceAppV1(api, authenticator, production_observability)
        return ServiceRuntime(
            config=config,
            store=store,
            projects=projects,
            capabilities=capabilities,
            agents=agents,
            dispatcher=dispatcher,
            kernel=kernel,
            human=human,
            approvals=approvals,
            workflows=workflows,
            releases=releases,
            telemetry=telemetry,
            production_metrics=production_metrics,
            production_observability=production_observability,
            health=health,
            qualifier=qualifier,
            authenticator=authenticator,
            api=api,
            app=app,
            project_factory=project_factory,
        )
    except BaseException:
        store.close()
        raise
