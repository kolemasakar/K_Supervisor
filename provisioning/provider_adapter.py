from integrations import AvailabilityState
from providers import ProviderRequest

from .contracts import ProvisioningKind, ProvisioningResult


class ProviderProvisioningAdapter:
    def __init__(self, provider, supported_kinds: tuple[ProvisioningKind, ...]):
        self.provider = provider
        self.provider_id = provider.descriptor.provider_id
        self.supported_kinds = supported_kinds

    def available(self) -> bool:
        return self.provider.check_availability().state != AvailabilityState.UNAVAILABLE

    def provision(self, request):
        response = self.provider.execute(
            ProviderRequest(
                project_id=request.project_id,
                operation="provision",
                payload={
                    "kind": request.kind.value,
                    "resource_name": request.resource_name,
                    "configuration": request.configuration,
                },
                access_refs=request.access_refs,
            )
        )
        data = response.payload
        return ProvisioningResult(
            resource_id=str(data["resource_id"]),
            locator=data.get("locator"),
            created=bool(data.get("created", True)),
            metadata=response.metadata,
        )
