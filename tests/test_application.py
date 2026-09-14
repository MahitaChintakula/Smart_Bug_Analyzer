from app.controller import ApplicationController


def main():

    controller = ApplicationController()

    query = "Login crashes because user object is null"

    report = controller.analyze(query)

    print("\n========== SMART BUG REPORT ==========\n")

    print("Severity :", report["severity"])
    print("Priority :", report["priority"])

    print("\nRoot Cause:")
    print(report["root_cause"])

    print("\nRecommended Fix:")
    print(report["recommendation"])

    print("\nSimilar Bugs:")

    for bug in report["similar"]:
        print(f"{bug.bug_id} | {bug.title} | {bug.similarity_score}")


if __name__ == "__main__":
    main()
