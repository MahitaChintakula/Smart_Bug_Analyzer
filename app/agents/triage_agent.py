from app.models.triage import TriageResult
from app.services.llm_service import LLMService


class TriageAgent:

    def __init__(self, llm_service=None):
        self.llm_service = llm_service or LLMService()

    def analyze(self, bug_report, root_cause):

        prompt = f"""
You are a software bug triage expert.

Analyze this bug.

BUG REPORT:
{bug_report}

ROOT CAUSE:
{root_cause}

Determine:

1. Severity: Critical, High, Medium, or Low
2. Priority: P1, P2, P3, or P4
3. Reason for your decision

Return ONLY this format:

SEVERITY:
<severity>

PRIORITY:
<priority>

REASON:
<short explanation>
"""

        answer = self.llm_service.generate(prompt, agent_name="Triage")

        return self._parse_response(answer)

    def _parse_response(self, answer):

        severity = "Medium"
        priority = "P3"
        reason = "Unable to determine priority."

        # Clean the response
        answer = answer.strip()

        if "SEVERITY:" in answer:

            severity = answer.split("SEVERITY:", 1)[1].split("PRIORITY:", 1)[0].strip()

        if "PRIORITY:" in answer:

            priority = answer.split("PRIORITY:", 1)[1].split("REASON:", 1)[0].strip()

        if "REASON:" in answer:

            reason = answer.split("REASON:", 1)[1].strip()

        return TriageResult(severity=severity, priority=priority, reason=reason)
