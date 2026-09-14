from app.controller import ApplicationController


def main():

    controller = ApplicationController()

    bug_report = """
java.lang.NullPointerException

at LoginService.java:45

at UserController.java:18
"""

    result = controller.analyze(bug_report)

    print("\n==============================")
    print("SMART BUG ANALYSIS")
    print("==============================")

    print("\nLOG INFORMATION:")
    print(result["log_info"])

    print("\nSIMILAR BUGS:")

    for bug in result["similar_bugs"]:
        print(bug)


if __name__ == "__main__":
    main()
