from app.agents.duplicate_agent import DuplicateDetectionAgent
from app.services.rag_service import RAGService


def main():

    rag = RAGService("data/resolved_bugs/resolved_bugs.json")

    agent = DuplicateDetectionAgent(rag)

    query = "Login crashes because user object is null"

    results = agent.analyze(query)

    for result in results:
        print(result)


if __name__ == "__main__":
    main()
