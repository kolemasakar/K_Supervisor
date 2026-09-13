from __future__ import annotations

from statistics import fmean

from models.agent import AgentRunRequest, AgentRunResult
from models.enums import ExecutionStatus
from runtime.contracts import ExecutionControl


def _success(request: AgentRunRequest, output: dict) -> AgentRunResult:
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
        output=output,
    )


class ResearchAgent:
    def __init__(self, provider_label: str = "reference"):
        self.provider_label = provider_label

    def __call__(self, request: AgentRunRequest, control: ExecutionControl) -> AgentRunResult:
        control.check_cancelled()
        query = str(request.input.get("query", "")).strip()
        raw_sources = request.input.get("sources", [])
        sources = raw_sources if isinstance(raw_sources, list) else []
        control.consume("sources", len(sources))
        summary = " | ".join(str(item) for item in sources[:3]) if sources else f"No supplied sources for: {query}"
        return _success(
            request,
            {
                "query": query,
                "summary": summary,
                "source_count": len(sources),
                "provider": self.provider_label,
            },
        )


class CriticAgent:
    def __call__(self, request: AgentRunRequest, control: ExecutionControl) -> AgentRunResult:
        control.check_cancelled()
        content = str(request.input.get("content", ""))
        issues: list[str] = []
        if not content.strip():
            issues.append("content is empty")
        if len(content.strip()) < 40 and content.strip():
            issues.append("content is very short")
        return _success(
            request,
            {
                "verdict": "REVISE" if issues else "PASS",
                "issues": issues,
            },
        )


class ReportAgent:
    def __call__(self, request: AgentRunRequest, control: ExecutionControl) -> AgentRunResult:
        control.check_cancelled()
        raw_sections = request.input.get("sections", [])
        sections = raw_sections if isinstance(raw_sections, list) else []
        report = "\n\n".join(str(item).strip() for item in sections if str(item).strip())
        return _success(request, {"report": report, "section_count": len(sections)})


class DataAnalysisAgent:
    def __call__(self, request: AgentRunRequest, control: ExecutionControl) -> AgentRunResult:
        control.check_cancelled()
        raw_values = request.input.get("values", [])
        values = [
            float(value)
            for value in raw_values
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ] if isinstance(raw_values, list) else []
        output = {
            "count": len(values),
            "sum": sum(values),
            "mean": fmean(values) if values else None,
        }
        return _success(request, output)


class FactCheckAgent:
    def __call__(self, request: AgentRunRequest, control: ExecutionControl) -> AgentRunResult:
        control.check_cancelled()
        claim = str(request.input.get("claim", "")).strip()
        raw_evidence = request.input.get("evidence", [])
        evidence = [str(item) for item in raw_evidence] if isinstance(raw_evidence, list) else []
        control.consume("sources", len(evidence))
        normalized = claim.casefold()
        supported = bool(normalized) and any(normalized in item.casefold() for item in evidence)
        return _success(
            request,
            {
                "claim": claim,
                "verdict": "SUPPORTED" if supported else "UNVERIFIED",
                "evidence_count": len(evidence),
            },
        )
