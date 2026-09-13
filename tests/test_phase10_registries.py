from integrations import AvailabilityState, DependencyRequirement, IntegrationKind
from providers import ModelProfile, ProviderDescriptor
from providers.model_hook import model_candidates
from registry import ProviderRegistry, ToolRegistry
from registry.dependencies import dependency_available
from tools import ToolDescriptor
from tests.phase10_support import FakeProvider, FakeTool


def test_tool_and_provider_registries_resolve_versions_and_dependencies():
    tools = ToolRegistry()
    tool_v1 = FakeTool(ToolDescriptor(tool_id="repo.read", version="1.0", operations=("read",)))
    tool_v2 = FakeTool(ToolDescriptor(tool_id="repo.read", version="2.0", operations=("read",)))
    tools.register(tool_v1)
    tools.register(tool_v2)
    assert tools.resolve("repo.read", "^1.0") is tool_v1
    assert tools.resolve("repo.read", ">=1.0") is tool_v2

    providers = ProviderRegistry()
    provider = FakeProvider(
        ProviderDescriptor(
            provider_id="model.test",
            version="1.0",
            provider_type="MODEL",
            operations=("generate",),
            models=(ModelProfile(model_id="m1", features=("text",), context_window=8192),),
        )
    )
    providers.register(provider)
    assert providers.resolve("model.test", "1.0", "generate") is provider

    requirement = DependencyRequirement(
        kind=IntegrationKind.TOOL,
        component_id="repo.read",
        version_constraint=">=2.0",
    )
    assert dependency_available(requirement, tools, providers)


def test_availability_and_model_candidates_stay_provider_independent():
    providers = ProviderRegistry()
    unavailable = FakeProvider(
        ProviderDescriptor(provider_id="offline", version="1.0", provider_type="SERVICE"),
        state=AvailabilityState.UNAVAILABLE,
    )
    providers.register(unavailable)
    assert unavailable.check_availability().state == AvailabilityState.UNAVAILABLE

    model_provider = FakeProvider(
        ProviderDescriptor(
            provider_id="models.a",
            version="2.0",
            provider_type="MODEL",
            models=(ModelProfile(model_id="alpha", features=("text", "tools"), priority=5),),
        )
    )
    providers.register(model_provider)
    candidates = model_candidates(providers)
    assert candidates == (
        {
            "provider_id": "models.a",
            "provider_version": "2.0",
            "model_id": "alpha",
            "features": ("text", "tools"),
            "context_window": None,
            "priority": 5,
        },
    )
