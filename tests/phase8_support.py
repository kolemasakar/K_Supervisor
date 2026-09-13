from models.agent import AgentRunRequest, AgentRunResult
from models.enums import ExecutionStatus
from registry import AgentRegistry, CapabilityRegistry
from runtime import AgentRuntimeDispatcher, InProcessRuntimeAdapter
from tests.phase5_support import make_agent, make_capability


def build_runtime(unavailable_after=3):
    capabilities = CapabilityRegistry()
    capabilities.register(make_capability())
    agents = AgentRegistry(capabilities)
    agents.register(make_agent("A1"))
    adapter = InProcessRuntimeAdapter()
    runtime = AgentRuntimeDispatcher(
        agents,
        adapter,
        unavailable_after=unavailable_after,
    )
    return agents, adapter, runtime


def make_request(*, run_id="RUN1", request_id="REQ1", key=None, limits=None, input_data=None):
    return AgentRunRequest(
        request_id=request_id,
        project_id="P1",
        task_id="T1",
        workflow_run_id="WF1",
        run_id=run_id,
        agent_id="A1",
        capability_id="analysis.test",
        capability_version="1.0.0",
        operation="run",
        input=input_data or {"value": 1},
        limits=limits or {},
        idempotency_key=key,
    )


def success(request, output=None):
    return AgentRunResult(
        request_id=request.request_id,
        project_id=request.project_id,
        task_id=request.task_id,
        workflow_run_id=request.workflow_run_id,
        run_id=request.run_id,
        agent_id=request.agent_id,
        capability_id=request.capability_id,
        capability_version=request.capability_version,
        status=ExecutionStatus.SUCCEEDED,
        output=output or {"ok": True},
    )
