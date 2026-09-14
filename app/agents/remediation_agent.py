from app.models.remediation import RemediationResult
from app.services.llm_service import LLMService


class RemediationAgent:

    def __init__(self, llm_service=None):
        self.llm_service = llm_service or LLMService()

    def analyze(self, bug_report, root_cause, historical_bugs):

        historical_context = ""

        for bug in historical_bugs:

            historical_context += f"""
Bug ID: {bug.bug_id}
Title: {bug.title}
Root Cause: {getattr(bug, "root_cause", "Not available")}
Resolution: {getattr(bug, "resolution", "Not available")}
-------------------------
"""

        prompt = f"""
You are an expert software engineer responsible for fixing bugs.

NEW BUG:
{bug_report}

ROOT CAUSE:
{root_cause}

HISTORICAL BUGS AND THEIR RESOLUTIONS:
{historical_context}

Recommend a practical and safe fix.

Return ONLY this format:

RECOMMENDED FIX:
<clear, specific recommended fix in 2-3 sentences, including what should change and why it addresses the root cause>

CODE SUGGESTION:
<a useful code snippet that implements the recommended fix for this bug. Use the most appropriate language from the report, do not wrap it in Markdown fences, and do not invent unrelated APIs.>

FIX CONFIDENCE:
<High, Medium, or Low, based on how directly the suggested fix addresses the root cause>

STEPS:
1. <step>
2. <step>
3. <step>

PREVENTION:
<a concrete prevention strategy in 2-3 sentences, including validation, testing, or monitoring where relevant>
"""

        answer = self.llm_service.generate(prompt, agent_name="Remediation")

        return self._parse_response(answer)

    def _parse_response(self, answer):

        recommended_fix = "No fix available."
        code_suggestion = "Code suggestion unavailable"
        fix_confidence = "Unavailable"
        steps = []
        prevention = "No prevention strategy available."

        answer = answer.strip()

        if "RECOMMENDED FIX:" in answer:

            recommended_fix = answer.split("RECOMMENDED FIX:", 1)[1]
            for marker in ("CODE SUGGESTION:", "STEPS:", "PREVENTION:"):
                recommended_fix = recommended_fix.split(marker, 1)[0]
            recommended_fix = recommended_fix.strip()

        if "CODE SUGGESTION:" in answer:

            code_suggestion = (
                answer.split("CODE SUGGESTION:", 1)[1]
                .split("FIX CONFIDENCE:", 1)[0]
                .strip()
            ) or "Code suggestion unavailable"

        if "FIX CONFIDENCE:" in answer:

            fix_confidence = (
                answer.split("FIX CONFIDENCE:", 1)[1].split("STEPS:", 1)[0].strip()
            ) or "Unavailable"

        if "STEPS:" in answer:

            steps_text = answer.split("STEPS:", 1)[1].split("PREVENTION:", 1)[0].strip()

            for line in steps_text.splitlines():

                line = line.strip()

                if line:
                    line = line.lstrip("0123456789.- ")

                    if line:
                        steps.append(line)

        if "PREVENTION:" in answer:

            prevention = answer.split("PREVENTION:", 1)[1].strip()

        return RemediationResult(
            recommended_fix=recommended_fix,
            code_suggestion=code_suggestion,
            fix_confidence=fix_confidence,
            steps=steps,
            prevention=prevention,
        )
