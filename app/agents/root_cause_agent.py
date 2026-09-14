from app.models.root_cause import RootCauseResult
from app.services.llm_service import LLMService


class RootCauseAgent:

    def __init__(self, llm_service=None):
        self.llm_service = llm_service or LLMService()

    def analyze(self, bug_report, similar_bugs):

        historical_context = ""

        for bug in similar_bugs:

            historical_context += f"""
Bug ID: {bug.bug_id}
Title: {bug.title}
Severity: {bug.severity}
Priority: {bug.priority}
Root Cause: {getattr(bug, "root_cause", "Not available")}
Resolution: {getattr(bug, "resolution", "Not available")}
-------------------------
"""

        prompt = f"""
You are an expert software debugging engineer.

Analyze this new bug report.

NEW BUG:
{bug_report}

HISTORICAL BUGS:
{historical_context}

Use the historical bugs as supporting evidence.

Determine the most probable root cause.

Return exactly:

ROOT CAUSE:
<short root cause>

EXPLANATION:
<clear, detailed explanation in 3-5 sentences. Explain the failure mechanism, connect it to the relevant historical evidence, and describe the impact.>

CONFIDENCE:
<number between 0 and 1>
"""

        answer = self.llm_service.generate(prompt, agent_name="Root Cause")

        return self._parse_response(answer)

    def _parse_response(self, answer):

        root_cause = "Unknown"
        explanation = "Unable to determine root cause."
        confidence = 0.5

        if "ROOT CAUSE:" in answer:

            root_cause = answer.split("ROOT CAUSE:")[1].split("EXPLANATION:")[0].strip()

        if "EXPLANATION:" in answer:

            explanation = (
                answer.split("EXPLANATION:")[1].split("CONFIDENCE:")[0].strip()
            )

        if "CONFIDENCE:" in answer:

            try:
                confidence = float(answer.split("CONFIDENCE:")[1].strip().split()[0])
            except (ValueError, IndexError):
                confidence = 0.5

        return RootCauseResult(
            root_cause=root_cause, explanation=explanation, confidence=confidence
        )
