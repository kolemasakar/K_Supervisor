from agent_factory import AgentBlueprint, AgentScaffolder, CapabilityBlueprint
from models.agent import AgentRunResult
from models.capability import CapabilityRequirement
from models.enums import ExecutionStatus

from tests.phase12_support import build_reference_stack


def test_new_agent_can_be_scaffolded_validated_registered_and_run(tmp_path):
    store, capabilities, agents, _, factory, _, kernel = build_reference_stack(tmp_path)
    blueprint = AgentBlueprint(
        agent_id="custom.echo.default",
        agent_type="ECHO",
        display_name="Custom Echo Agent",
        class_name="EchoAgent",
        capabilities=(
            CapabilityBlueprint(
                capability_id="custom.echo",
                description="Return supplied payload for factory validation.",
                operations=("run",),
                input_schema="schema://custom/echo/input",
                output_schema="schema://custom/echo/output",
            ),
        ),
    )

    scaffolder = AgentScaffolder()
    rendered = scaffolder.render(blueprint)
    report = scaffolder.validate(rendered)
    assert report.valid
    written = scaffolder.write(tmp_path / "generated-agent", blueprint)
    assert {path.name for path in written} == {"agent.py", "test_agent.py", "README.md"}
    assert scaffolder.write(tmp_path / "generated-agent", blueprint) == written

    def handler(request, control):
        control.check_cancelled()
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
            output={"echo": request.input},
        )

    factory.register(blueprint, handler)
    assert capabilities.get("custom.echo", "1.0.0") is not None
    assert agents.get("custom.echo.default") is not None

    result = kernel.run_task(
        "P12",
        "custom echo",
        CapabilityRequirement(
            capability_id="custom.echo",
            version_constraint="^1.0.0",
            operation="run",
        ),
        {"value": 42},
    )
    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.output == {"echo": {"value": 42}}
    store.close()
