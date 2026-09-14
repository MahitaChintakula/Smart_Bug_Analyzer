from app.agents.triage_agent import TriageAgent


def main():

    agent = TriageAgent()

    bug_report = """
Login crashes when the user tries to sign in.
The user object is null.
"""

    root_cause = """
The login service attempts to access the user object
before validating that it exists.
"""

    result = agent.analyze(bug_report, root_cause)

    print("\n========== TRIAGE RESULT ==========")

    print("\nSeverity:")
    print(result.severity)

    print("\nPriority:")
    print(result.priority)

    print("\nReason:")
    print(result.reason)


if __name__ == "__main__":
    main()
