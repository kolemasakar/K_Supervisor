from __future__ import annotations

from agent_factory import AgentBlueprint, AgentFactory, CapabilityBlueprint

from .reference import CriticAgent, DataAnalysisAgent, FactCheckAgent, ReportAgent, ResearchAgent


def _capability(
    capability_id: str,
    description: str,
    *,
    input_schema: str,
    output_schema: str,
) -> CapabilityBlueprint:
    return CapabilityBlueprint(
        capability_id=capability_id,
        capability_version="1.0.0",
        description=description,
        operations=("run",),
        input_schema=input_schema,
        output_schema=output_schema,
        side_effects=("NONE",),
        risk_class="LOW",
        metadata={"reference": True},
    )


_RESEARCH = _capability(
    "research.reference",
    "Summarize research material supplied in the request without external side effects.",
    input_schema="schema://reference/research/input",
    output_schema="schema://reference/research/output",
)


def reference_agent_entries():
    return (
        (
            AgentBlueprint(
                agent_id="reference.research.alpha",
                agent_type="RESEARCH",
                display_name="Reference Research Agent Alpha",
                class_name="ResearchAgent",
                capabilities=(_RESEARCH,),
                metadata={"reference": True, "provider_label": "alpha"},
            ),
            ResearchAgent("alpha"),
        ),
        (
            AgentBlueprint(
                agent_id="reference.research.beta",
                agent_type="RESEARCH",
                display_name="Reference Research Agent Beta",
                class_name="ResearchAgent",
                capabilities=(_RESEARCH,),
                metadata={"reference": True, "provider_label": "beta"},
            ),
            ResearchAgent("beta"),
        ),
        (
            AgentBlueprint(
                agent_id="reference.critic.default",
                agent_type="CRITIC",
                display_name="Reference Critic Agent",
                class_name="CriticAgent",
                capabilities=(
                    _capability(
                        "critique.reference",
                        "Perform deterministic structural critique of supplied content.",
                        input_schema="schema://reference/critique/input",
                        output_schema="schema://reference/critique/output",
                    ),
                ),
                metadata={"reference": True},
            ),
            CriticAgent(),
        ),
        (
            AgentBlueprint(
                agent_id="reference.report.default",
                agent_type="REPORT",
                display_name="Reference Report Agent",
                class_name="ReportAgent",
                capabilities=(
                    _capability(
                        "report.reference",
                        "Compose supplied sections into a deterministic report.",
                        input_schema="schema://reference/report/input",
                        output_schema="schema://reference/report/output",
                    ),
                ),
                metadata={"reference": True},
            ),
            ReportAgent(),
        ),
        (
            AgentBlueprint(
                agent_id="reference.analysis.default",
                agent_type="DATA_ANALYSIS",
                display_name="Reference Data Analysis Agent",
                class_name="DataAnalysisAgent",
                capabilities=(
                    _capability(
                        "analysis.reference",
                        "Calculate basic deterministic statistics over supplied numeric values.",
                        input_schema="schema://reference/analysis/input",
                        output_schema="schema://reference/analysis/output",
                    ),
                ),
                metadata={"reference": True},
            ),
            DataAnalysisAgent(),
        ),
        (
            AgentBlueprint(
                agent_id="reference.factcheck.default",
                agent_type="FACT_CHECK",
                display_name="Reference Fact Check Agent",
                class_name="FactCheckAgent",
                capabilities=(
                    _capability(
                        "factcheck.reference",
                        "Check whether supplied evidence explicitly contains the supplied claim.",
                        input_schema="schema://reference/factcheck/input",
                        output_schema="schema://reference/factcheck/output",
                    ),
                ),
                metadata={"reference": True},
            ),
            FactCheckAgent(),
        ),
    )


def register_reference_agents(factory: AgentFactory):
    return tuple(factory.register(blueprint, handler) for blueprint, handler in reference_agent_entries())
