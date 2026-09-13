from datetime import datetime, timezone

from integrations import AvailabilityReport, AvailabilityState
from providers import ProviderDescriptor, ProviderResponse
from tools import ToolDescriptor, ToolResult

NOW = datetime(2026, 9, 13, 18, 30, tzinfo=timezone.utc)


class FakeTool:
    def __init__(self, descriptor: ToolDescriptor, state=AvailabilityState.AVAILABLE):
        self.descriptor = descriptor
        self.state = state
        self.requests = []

    def check_availability(self):
        return AvailabilityReport(
            component_id=self.descriptor.tool_id,
            state=self.state,
            checked_at=NOW,
        )

    def invoke(self, request):
        self.requests.append(request)
        return ToolResult(output={"operation": request.operation})


class FakeProvider:
    def __init__(
        self,
        descriptor: ProviderDescriptor,
        state=AvailabilityState.AVAILABLE,
        response=None,
    ):
        self.descriptor = descriptor
        self.state = state
        self.response = response or ProviderResponse(payload={"ok": True})
        self.requests = []

    def check_availability(self):
        return AvailabilityReport(
            component_id=self.descriptor.provider_id,
            state=self.state,
            checked_at=NOW,
        )

    def execute(self, request):
        self.requests.append(request)
        return self.response
