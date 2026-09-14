from time import perf_counter

from models.capability import CapabilityRequirement
from supervisor.routing import ProviderRouter
from tests.phase12_support import build_reference_stack


def test_provider_routing_performance_baseline(tmp_path):
    _, _, agents, _, _, _, _ = build_reference_stack(tmp_path)
    requirement = CapabilityRequirement(
        capability_id="research.reference",
        version_constraint="1.0.0",
        operation="run",
    )
    providers = agents.find_providers(requirement)
    router = ProviderRouter()
    started = perf_counter()
    for _ in range(10_000):
        router.select(requirement, providers)
    elapsed = perf_counter() - started
    assert elapsed < 3.0
