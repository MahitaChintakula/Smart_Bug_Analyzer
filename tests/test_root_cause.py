from app.agents.root_cause_agent import RootCauseAgent
from app.rag.knowledge_base import KnowledgeBase


def main():

    kb = KnowledgeBase("data/resolved_bugs/resolved_bugs.json")

    bugs = kb.load_bugs()

    agent = RootCauseAgent()

    bug_report = """
java.lang.NullPointerException

at LoginService.java:45

Login crashes because the user object is null.
"""

    result = agent.analyze(bug_report, bugs[:2])

    print("\n========== ROOT CAUSE ==========")

    print("Root Cause:")
    print(result.root_cause)

    print("\nExplanation:")
    print(result.explanation)

    print("\nConfidence:")
    print(result.confidence)


if __name__ == "__main__":
    main()
