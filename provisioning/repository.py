from factory.contracts import RepositoryTarget

from .contracts import ProvisioningKind, ProvisioningResult


class RepositoryProvisioningAdapter:
    supported_kinds = (ProvisioningKind.REPOSITORY,)

    def __init__(self, adapter):
        self.adapter = adapter
        self.provider_id = adapter.provider

    def available(self) -> bool:
        return True

    def provision(self, request):
        target = RepositoryTarget(
            provider=self.provider_id,
            owner=None,
            name=request.resource_name,
            visibility="PRIVATE",
            url=None,
            default_branch="main",
            ci_required=True,
            provisioning="AUTOMATABLE",
        )
        repository = self.adapter.prepare(target)
        return ProvisioningResult(
            resource_id=repository.repository_id,
            locator=repository.locator,
            created=repository.created,
        )
