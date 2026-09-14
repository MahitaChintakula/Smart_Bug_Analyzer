"""Context-aware follow-up chat for a completed bug analysis."""

from collections.abc import Mapping, Sequence

from app.services.llm_service import LLMService


class ChatService:
    """Answer follow-up questions using one analysis and its conversation history."""

    def __init__(self, llm_service: LLMService | None = None):
        # The caller owns this request-scoped service.  LLMService keeps the
        # existing Gemini -> Groq -> Ollama fallback and provider lock.
        self.llm_service = llm_service or LLMService()

    def answer(
        self,
        analysis: Mapping[str, object],
        messages: Sequence[Mapping[str, object]],
        user_message: str,
    ) -> str:
        question = str(user_message or "").strip()
        if not question:
            raise ValueError("A chat message is required.")

        prompt = self._build_prompt(analysis, messages, question)
        return self.llm_service.generate(prompt, agent_name="Chatbot")

    def _build_prompt(
        self,
        analysis: Mapping[str, object],
        messages: Sequence[Mapping[str, object]],
        question: str,
    ) -> str:
        log_info = self._mapping(analysis.get("log_info"))
        root_cause = self._mapping(analysis.get("root_cause"))
        triage = self._mapping(analysis.get("triage"))
        remediation = self._mapping(analysis.get("remediation"))
        similar_bugs = analysis.get("similar_bugs")
        similar_text = self._similar_bugs(similar_bugs)
        summary = analysis.get("overall_summary") or (
            f"{self._clip(root_cause.get('root_cause'), 300)}; "
            f"{self._clip(triage.get('severity'))} severity / "
            f"{self._clip(triage.get('priority'))} priority; "
            f"recommended fix: {self._clip(remediation.get('recommended_fix'), 700)}"
        )

        history_lines = []
        for message in list(messages or [])[-8:]:
            item = self._mapping(message)
            role = str(item.get("role", "user")).strip().lower()
            role = "Assistant" if role == "assistant" else "Developer"
            content = self._clip(item.get("content"), 600)
            if content:
                history_lines.append(f"{role}: {content}")
        history = "\n".join(history_lines) or "(no previous conversation)"

        return f"""You are the Smart Bug Analyzer follow-up assistant.
Answer the developer's question using only the completed analysis below and the conversation history. Be concise, practical, and explain uncertainty when the evidence is limited. Do not claim that you changed code or ran commands. If the question is outside this bug, say so briefly and ask for relevant details.

CURRENT BUG REPORT:
{self._clip(analysis.get('bug_report'), 1800)}

LOG ANALYSIS:
Exception: {self._clip(log_info.get('exception'))}
File: {self._clip(log_info.get('file'))}
Line: {self._clip(log_info.get('line'))}

ROOT CAUSE:
{self._clip(root_cause.get('root_cause'))}
Explanation: {self._clip(root_cause.get('explanation'), 1000)}
Confidence: {self._clip(root_cause.get('confidence'))}

SIMILAR HISTORICAL BUGS (top results):
{similar_text}

TRIAGE:
Severity: {self._clip(triage.get('severity'))}
Priority: {self._clip(triage.get('priority'))}
Reason: {self._clip(triage.get('reason'), 700)}

REMEDIATION:
Recommended fix: {self._clip(remediation.get('recommended_fix'), 1000)}
Code suggestion: {self._clip(remediation.get('code_suggestion'), 1000)}
Fix confidence: {self._clip(remediation.get('fix_confidence'))}
Steps: {self._clip(remediation.get('steps'), 900)}
Prevention: {self._clip(remediation.get('prevention'), 700)}

OVERALL SUMMARY:
{self._clip(summary, 1200)}

PREVIOUS CONVERSATION:
{history}

DEVELOPER QUESTION:
{question}

ASSISTANT ANSWER:
"""

    def _similar_bugs(self, value: object) -> str:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return "(none)"
        rows = []
        for bug in list(value)[:3]:
            item = self._mapping(bug)
            rows.append(
                f"{self._clip(item.get('bug_id'))} — "
                f"{self._clip(item.get('title'), 180)}; "
                f"similarity {self._clip(item.get('similarity_score'))}; "
                f"resolution {self._clip(item.get('resolution'), 500)}"
            )
        return "\n".join(rows) or "(none)"

    @staticmethod
    def _mapping(value: object) -> Mapping[str, object]:
        if isinstance(value, Mapping):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        return {}

    @staticmethod
    def _clip(value: object, limit: int = 500) -> str:
        if value is None:
            return "Not available"
        if isinstance(value, (list, tuple)):
            text = "; ".join(str(item) for item in value)
        else:
            text = str(value)
        text = " ".join(text.split())
        if not text:
            return "Not available"
        return text if len(text) <= limit else f"{text[:limit - 1]}…"
