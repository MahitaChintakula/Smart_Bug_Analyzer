import json
import tempfile
import unittest
from pathlib import Path

from app.agents.orchestrator import BugOrchestrator
from app.models.log_info import LogInfo
from app.models.remediation import RemediationResult
from app.models.root_cause import RootCauseResult
from app.models.search_result import SearchResult
from app.models.triage import TriageResult
from app.rag.knowledge_base import KnowledgeBase
from app.rag.retriever import RAGService
from app.rag.vector_store import VectorStore


class _Parser:
    def parse(self, _report):
        return LogInfo(
            exception="CacheMissException",
            file="PreferenceCache.java",
            line=42,
        )


class _DuplicateAgent:
    def __init__(self, similarity):
        self.similarity = similarity

    def analyze(self, _report):
        return [
            SearchResult(
                bug_id="BUG-001",
                title="Existing bug",
                severity="High",
                priority="P2",
                similarity_score=self.similarity,
            )
        ]


class _RootCauseAgent:
    def analyze(self, _report, _historical_context):
        return RootCauseResult(
            root_cause="Cache invalidation is missing.",
            explanation="The cache keeps stale values.",
            confidence=0.88,
        )


class _TriageAgent:
    def analyze(self, _report, _root_cause):
        return TriageResult(
            severity="High",
            priority="P2",
            reason="Stale preferences affect user behavior.",
        )


class _RemediationAgent:
    def analyze(self, _report, _root_cause, _historical_context):
        return RemediationResult(
            recommended_fix="Invalidate the cache after preference updates.",
            steps=["Add cache invalidation"],
            prevention="Add cache consistency tests.",
        )


class _FakeRAG:
    def __init__(self, bugs):
        self.bugs = bugs
        self.added = []

    def add_bug(self, bug):
        self.bugs.append(bug)
        self.added.append(bug.bug_id)
        return True


class KnowledgeBaseGrowthTests(unittest.TestCase):
    def _controller_parts(self, path, similarity):
        knowledge_base = KnowledgeBase(path)
        historical_bugs = knowledge_base.load_bugs()
        rag_service = _FakeRAG(historical_bugs)
        orchestrator = BugOrchestrator(
            parser=_Parser(),
            duplicate_agent=_DuplicateAgent(similarity),
            root_cause_agent=_RootCauseAgent(),
            triage_agent=_TriageAgent(),
            remediation_agent=_RemediationAgent(),
            historical_bugs=historical_bugs,
            knowledge_base=knowledge_base,
            rag_service=rag_service,
        )
        return orchestrator, rag_service

    def test_new_bug_is_saved_once_with_next_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resolved_bugs.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "bug_id": "BUG-050",
                            "title": "Existing bug",
                            "description": "old",
                            "severity": "High",
                            "priority": "P2",
                            "module": "Old",
                            "exception": "OldException",
                            "stack_trace": "old",
                            "root_cause": "old",
                            "resolution": "old",
                            "tags": ["old"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            orchestrator, rag_service = self._controller_parts(path, 0.30)
            orchestrator.analyze("A new preference cache bug")
            orchestrator.duplicate_agent.similarity = 0.90
            orchestrator.analyze("The same new preference cache bug")

            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 2)
            self.assertEqual(data[-1]["bug_id"], "BUG-051")
            self.assertEqual(data[-1]["exception"], "CacheMissException")
            self.assertEqual(rag_service.added, ["BUG-051"])

    def test_sufficient_similarity_skips_insertion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resolved_bugs.json"
            path.write_text("[]", encoding="utf-8")
            orchestrator, rag_service = self._controller_parts(path, 0.90)

            orchestrator.analyze("An existing bug")

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])
            self.assertEqual(rag_service.added, [])

    def test_live_faiss_index_accepts_new_bug(self):
        class _Embedder:
            def encode(self, text):
                return [1.0, 0.0, 0.0] if "new-indexed" in text else [0.0, 1.0, 0.0]

        service = RAGService.__new__(RAGService)
        service.bugs = []
        service.embedding_generator = _Embedder()
        service.vector_store = VectorStore(3)

        class _Bug:
            bug_id = "BUG-051"
            title = "new-indexed"
            description = "new"
            severity = "High"
            priority = "P2"
            module = "New"
            exception = "NewException"
            stack_trace = "new"
            root_cause = "new"
            resolution = "new"

        self.assertTrue(service.add_bug(_Bug()))
        self.assertFalse(service.add_bug(_Bug()))
        _, indices = service.vector_store.search([1.0, 0.0, 0.0], k=1)
        self.assertEqual(int(indices[0][0]), 0)


if __name__ == "__main__":
    unittest.main()
