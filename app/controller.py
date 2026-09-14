# # from app.services.rag_service import RAGService
# # from app.agents.duplicate_agent import DuplicateDetectionAgent
# # from app.agents.root_cause_agent import RootCauseAgent
# # from app.agents.triage_agent import TriageAgent
# # from app.agents.remediation_agent import RemediationAgent


# # class ApplicationController:

# #     def __init__(self):

# #         self.rag = RAGService(
# #             "data/resolved_bugs/resolved_bugs.json"
# #         )

# #         self.duplicate = DuplicateDetectionAgent(self.rag)

# #         self.root = RootCauseAgent()

# #         self.triage = TriageAgent()

# #         self.remedy = RemediationAgent()

# #     def analyze(self, query):

# #         similar = self.duplicate.analyze(query)

# #         root = self.root.analyze(similar)

# #         triage = self.triage.analyze(similar)

# #         remedy = self.remedy.analyze(similar)

# #         return {
# #             "similar": similar,
# #             "root_cause": root,
# #             "severity": triage["severity"],
# #             "priority": triage["priority"],
# #             "recommendation": remedy
# #         }
# from app.parser.log_parser import LogParser
# from app.services.rag_service import RAGService
# from app.agents.duplicate_agent import DuplicateDetectionAgent


# class ApplicationController:

#     def __init__(self):

#         self.rag_service = RAGService(
#             "data/resolved_bugs/resolved_bugs.json"
#         )

#         self.log_parser = LogParser()

#         self.duplicate_agent = DuplicateDetectionAgent(
#             self.rag_service
#         )

#     def analyze(self, bug_report):

#         # 1. Parse log
#         parsed_log = self.log_parser.parse(bug_report)

#         # 2. Find similar bugs
#         similar_bugs = self.duplicate_agent.analyze(
#             bug_report
#         )

#         return {
#             "bug_report": bug_report,
#             "log_info": parsed_log,
#             "similar_bugs": similar_bugs
#         }

from app.agents.orchestrator import BugOrchestrator

from app.agents.duplicate_agent import DuplicateDetectionAgent
from app.agents.root_cause_agent import RootCauseAgent
from app.agents.triage_agent import TriageAgent
from app.agents.remediation_agent import RemediationAgent

from app.parser.log_parser import LogParser

from app.rag.knowledge_base import KnowledgeBase
from app.rag.retriever import RAGService
from app.services.llm_service import LLMService


class BugController:

    def __init__(self):

        # ---------------------------------------------
        # Load historical bugs
        # ---------------------------------------------

        self.knowledge_base = KnowledgeBase("data/resolved_bugs/resolved_bugs.json")

        self.historical_bugs = self.knowledge_base.load_bugs()

        # ---------------------------------------------
        # Create RAG service
        # ---------------------------------------------

        self.rag_service = RAGService(self.historical_bugs)

        # ---------------------------------------------
        # Create agents
        # ---------------------------------------------

        self.duplicate_agent = DuplicateDetectionAgent(self.rag_service)

        # One request-scoped service selects the provider once and is shared
        # by all reasoning agents in this analysis.
        self.llm_service = LLMService()

        self.root_cause_agent = RootCauseAgent(llm_service=self.llm_service)

        self.triage_agent = TriageAgent(llm_service=self.llm_service)

        self.remediation_agent = RemediationAgent(llm_service=self.llm_service)

        # ---------------------------------------------
        # Create parser
        # ---------------------------------------------

        self.parser = LogParser()

        # ---------------------------------------------
        # Create orchestrator
        # ---------------------------------------------

        self.orchestrator = BugOrchestrator(
            parser=self.parser,
            duplicate_agent=self.duplicate_agent,
            root_cause_agent=self.root_cause_agent,
            triage_agent=self.triage_agent,
            remediation_agent=self.remediation_agent,
            historical_bugs=self.historical_bugs,
            knowledge_base=self.knowledge_base,
            rag_service=self.rag_service,
        )

    def analyze(self, bug_report):

        return self.orchestrator.analyze(bug_report)
