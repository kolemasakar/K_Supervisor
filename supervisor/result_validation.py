from models.agent import AgentRunRequest, AgentRunResult


class AgentResultContractError(ValueError):
    pass


def validate_result_matches_request(request: AgentRunRequest, result: AgentRunResult) -> None:
    fields = (
        "request_id",
        "project_id",
        "task_id",
        "workflow_run_id",
        "run_id",
        "agent_id",
        "capability_id",
        "capability_version",
    )
    mismatches = [name for name in fields if getattr(request, name) != getattr(result, name)]
    if mismatches:
        raise AgentResultContractError(
            "agent result correlation mismatch: " + ", ".join(mismatches)
        )
