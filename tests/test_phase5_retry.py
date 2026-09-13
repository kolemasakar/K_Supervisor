from models.agent import AgentError, AgentRunResult
from models.enums import ExecutionStatus
from supervisor.kernel import RetryPolicy, SupervisorKernel
from tests.phase5_support import build_stack, make_agent, make_requirement, success


def test_retryable_result_retries_once(tmp_path):
    store, projects, agents, dispatcher, _ = build_stack(tmp_path)
    agents.register(make_agent("agent.retry"))
    calls = []

    def handler(request):
        calls.append(request.run_id)
        if len(calls) == 1:
            return AgentRunResult(request_id=request.request_id, project_id=request.project_id,
                task_id=request.task_id, workflow_run_id=request.workflow_run_id, run_id=request.run_id,
                agent_id=request.agent_id, capability_id=request.capability_id,
                capability_version=request.capability_version, status=ExecutionStatus.FAILED,
                error=AgentError(code="TEMP", category="EXECUTION_ERROR", message="retry", retryable=True))
        return success(request)

    dispatcher.register("agent.retry", handler)
    kernel = SupervisorKernel(projects, agents, store, dispatcher, retry_policy=RetryPolicy(max_attempts=2))
    result = kernel.run_task("P1", "retry", make_requirement(), {})
    assert result.status == ExecutionStatus.SUCCEEDED
    assert len(calls) == 2
    assert len(store.list_agent_runs("P1")) == 2
    store.close()
