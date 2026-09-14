from app.agents.remediation_agent import RemediationAgent
from app.rag.knowledge_base import KnowledgeBase


def main():

    kb = KnowledgeBase("data/resolved_bugs/resolved_bugs.json")

    bugs = kb.load_bugs()

    agent = RemediationAgent()

    bug_report = """
Login crashes when the user tries to sign in.
The user object is null.
"""

    root_cause = """
The login service attempts to access the user object
before checking whether it exists.
"""

    result = agent.analyze(bug_report, root_cause, bugs[:2])

    print("\n========== REMEDIATION RESULT ==========")

    print("\nRecommended Fix:")
    print(result.recommended_fix)

    print("\nSteps:")

    for index, step in enumerate(result.steps, 1):
        print(f"{index}. {step}")

    print("\nPrevention:")
    print(result.prevention)


if __name__ == "__main__":
    main()
