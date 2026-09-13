from pathlib import Path

from access import AccessReference
from factory import FilesystemRepositoryAdapter
from providers import ProviderDescriptor, ProviderResponse
from provisioning import (
    ProviderProvisioningAdapter,
    ProvisioningKind,
    ProvisioningRegistry,
    ProvisioningRequest,
    RepositoryProvisioningAdapter,
)
from tests.phase10_support import FakeProvider


def test_repository_provisioning_adapter_is_replaceable(tmp_path):
    adapter = RepositoryProvisioningAdapter(FilesystemRepositoryAdapter(tmp_path / "repos"))
    registry = ProvisioningRegistry()
    registry.register(adapter)

    resolved = registry.resolve("FILESYSTEM", ProvisioningKind.REPOSITORY)
    result = resolved.provision(
        ProvisioningRequest(
            project_id="P10",
            kind=ProvisioningKind.REPOSITORY,
            provider_id="FILESYSTEM",
            resource_name="demo",
        )
    )
    assert result.created
    assert Path(result.locator, ".git").is_dir()


def test_provider_provisioning_forwards_only_access_references():
    provider = FakeProvider(
        ProviderDescriptor(
            provider_id="cloud.test",
            version="1.0",
            provider_type="CLOUD",
            operations=("provision",),
        ),
        response=ProviderResponse(
            payload={"resource_id": "db-1", "locator": "cloud://db-1", "created": True}
        ),
    )
    adapter = ProviderProvisioningAdapter(provider, (ProvisioningKind.DATABASE,))
    reference = AccessReference(uri="secret://project/P10/cloud")
    result = adapter.provision(
        ProvisioningRequest(
            project_id="P10",
            kind=ProvisioningKind.DATABASE,
            provider_id="cloud.test",
            resource_name="primary-db",
            access_refs=(reference,),
        )
    )
    assert result.resource_id == "db-1"
    assert provider.requests[0].access_refs == (reference,)
    assert "secret://" not in str(provider.requests[0].payload)
