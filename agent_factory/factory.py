from __future__ import annotations

from typing import Protocol

from models.agent import AgentDescriptor, AgentRunRequest, AgentRunResult, CapabilityRef
from models.capability import CapabilityDescriptor
from registry.agent_registry import AgentRegistry
from registry.capability_registry import CapabilityRegistry
from runtime.contracts import ExecutionControl

from .contracts import AgentBlueprint, AgentBuild


class RuntimeBindingTarget(Protocol):
    def register(
        self,
        agent_id: str,
        handler,
    ) -> None: ...


class AgentFactory:
    def __init__(
        self,
        capabilities: CapabilityRegistry,
        agents: AgentRegistry,
        runtime: RuntimeBindingTarget | None = None,
    ):
        self.capabilities = capabilities
        self.agents = agents
        self.runtime = runtime

    def build(self, blueprint: AgentBlueprint) -> AgentBuild:
        capability_descriptors = tuple(
            CapabilityDescriptor(
                capability_id=item.capability_id,
                capability_version=item.capability_version,
                description=item.description,
                operations=item.operations,
                input_schema=item.input_schema,
                output_schema=item.output_schema,
                constraints=item.constraints,
                requires=item.requires,
                side_effects=item.side_effects,
                risk_class=item.risk_class,
                metadata=item.metadata,
            )
            for item in blueprint.capabilities
        )
        descriptor = AgentDescriptor(
            agent_id=blueprint.agent_id,
            agent_type=blueprint.agent_type,
            agent_version=blueprint.agent_version,
            contract_version=blueprint.contract_version,
            display_name=blueprint.display_name,
            capabilities=tuple(
                CapabilityRef(
                    capability_id=item.capability_id,
                    capability_version=item.capability_version,
                )
                for item in capability_descriptors
            ),
            execution_mode=blueprint.execution_mode,
            status=blueprint.status,
            metadata={**blueprint.metadata, "factory_class_name": blueprint.class_name},
        )
        return AgentBuild(agent=descriptor, capabilities=capability_descriptors)

    def register(self, blueprint: AgentBlueprint, handler=None) -> AgentBuild:
        build = self.build(blueprint)
        for capability in build.capabilities:
            self.capabilities.register(capability)
        self.agents.register(build.agent)
        if handler is not None:
            if self.runtime is None:
                raise RuntimeError("runtime binding target is required when handler is supplied")
            self.runtime.register(build.agent.agent_id, handler)
        return build
