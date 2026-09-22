from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys

from access import EnvironmentSecretBackend, SecretBackend
from factory import FilesystemRepositoryAdapter, ProjectFactory
from factory.governed_github import build_governed_github_repository_adapter
from observability import (
    DeploymentQualifier,
    ProductionMetricRegistry,
    ProductionObservability,
    ServiceHealthEvaluator,
    StructuredLogger,
    TelemetryRecorder,
)
from persistence import SQLitePersistenceStore
from policy.approval import PolicyApprovalBroker
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry
from supervisor.dispatch import LocalAgentDispatcher
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.kernel import SupervisorKernel
from workflows import HumanInterventionApprovalRequester, WorkflowEngine

from .auth import StaticBearerAuthenticator
from .contracts import ServicePrincipal
from .service import ServiceApiV1
from .wsgi import WsgiServiceAppV1


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


def build_service_runtime(config, *, secret_backend: SecretBackend | None = None) -> ServiceRuntime:
    host = config.service_host
    if host is None:
        raise ValueError("service_host configuration is required for serve")
    if not host.principals:
        raise ValueError("service_host requires at least one authenticated principal")

    store = SQLitePersistenceStore(config.state_db_path)
    try:
        store.initialize()
        projects = ProjectRegistry(store)
        capabilities = CapabilityRegistry()
        agents = AgentRegistry(capabilities)
        dispatcher = LocalAgentDispatcher()
        kernel = SupervisorKernel(projects, agents, store, dispatcher)
        human = HumanInterventionBroker(store, projects)
        approvals = PolicyApprovalBroker(store, agents, human)
        workflows = WorkflowEngine(
            kernel,
            store,
            HumanInterventionApprovalRequester(human),
        )
        telemetry = TelemetryRecorder(store)
        production_metrics = ProductionMetricRegistry()
        production_observability = ProductionObservability(
            telemetry=telemetry,
            logger=StructuredLogger(sys.stderr),
            metrics=production_metrics,
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

        backend = secret_backend or EnvironmentSecretBackend()
        repository_root = Path(config.state_db_path).resolve().parent / "repositories"
        github_repository = build_governed_github_repository_adapter(
            store,
            projects,
            human,
            backend,
            observability=production_observability,
        )
        project_factory = ProjectFactory(
            projects,
            (
                FilesystemRepositoryAdapter(repository_root),
                github_repository,
            ),
            human,
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
