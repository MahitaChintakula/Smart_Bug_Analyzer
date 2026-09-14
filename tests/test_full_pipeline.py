from app.controller import BugController


def main():

    controller = BugController()

    bug_report = """
java.lang.NullPointerException

at LoginService.java:45

Login crashes because the user object is null.
"""

    result = controller.analyze(bug_report)

    print("\n")
    print("=" * 60)
    print("          SMART BUG ANALYZER")
    print("=" * 60)

    print("\nBUG REPORT:")
    print(result["bug_report"])

    print("\nLOG INFORMATION:")
    print(result["log_info"])

    print("\nSIMILAR BUGS:")

    for bug in result["similar_bugs"]:
        print(f"{bug.bug_id} | " f"{bug.title} | " f"{bug.similarity_score}")

    print("\nROOT CAUSE:")
    print(result["root_cause"].root_cause)

    print("\nEXPLANATION:")
    print(result["root_cause"].explanation)

    print("\nCONFIDENCE:")
    print(result["root_cause"].confidence)

    print("\nTRIAGE:")

    print("Severity:", result["triage"].severity)

    print("Priority:", result["triage"].priority)

    print("Reason:", result["triage"].reason)

    print("\nRECOMMENDED FIX:")
    print(result["remediation"].recommended_fix)

    print("\nFIX STEPS:")

    for index, step in enumerate(result["remediation"].steps, 1):
        print(f"{index}. {step}")

    print("\nPREVENTION:")
    print(result["remediation"].prevention)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
