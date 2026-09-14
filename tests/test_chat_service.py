import unittest

from app.services.chat_service import ChatService


class FakeLLM:
    def __init__(self):
        self.prompt = None
        self.agent_name = None

    def generate(self, prompt, agent_name=None):
        self.prompt = prompt
        self.agent_name = agent_name
        return "Check the database timeout and apply the recommended pool fix."


class ChatServiceTests(unittest.TestCase):
    def test_prompt_contains_analysis_and_recent_conversation(self):
        llm = FakeLLM()
        service = ChatService(llm)
        analysis = {
            "bug_report": "TimeoutError in reports.py line 42",
            "log_info": {"exception": "TimeoutError", "file": "reports.py", "line": 42},
            "root_cause": {
                "root_cause": "The connection pool is exhausted.",
                "explanation": "Sessions are not released after long queries.",
                "confidence": 0.88,
            },
            "similar_bugs": [
                {
                    "bug_id": "BUG-075",
                    "title": "SQLAlchemy connection pool timeout",
                    "similarity_score": 0.91,
                    "resolution": "Close sessions in finally blocks.",
                }
            ],
            "triage": {
                "severity": "High",
                "priority": "P1",
                "reason": "Reports are unavailable.",
            },
            "remediation": {
                "recommended_fix": "Release every session after use.",
                "code_suggestion": "with Session() as session:",
                "fix_confidence": "High",
                "steps": ["Add a context manager"],
                "prevention": "Add pool exhaustion monitoring.",
            },
        }

        answer = service.answer(
            analysis,
            [{"role": "user", "content": "What does the P1 priority mean?"}],
            "Which fix should I implement first?",
        )

        self.assertIn("Which fix should I implement first?", llm.prompt)
        self.assertIn("BUG-075", llm.prompt)
        self.assertIn("What does the P1 priority mean?", llm.prompt)
        self.assertEqual(llm.agent_name, "Chatbot")
        self.assertIn("pool fix", answer)

    def test_empty_question_is_rejected(self):
        with self.assertRaises(ValueError):
            ChatService(FakeLLM()).answer({}, [], "  ")


if __name__ == "__main__":
    unittest.main()
