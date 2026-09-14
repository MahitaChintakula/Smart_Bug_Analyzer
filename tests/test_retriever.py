from app.rag.knowledge_base import KnowledgeBase
from app.rag.retriever import RAGService


def main():

    # Load historical bugs
    kb = KnowledgeBase("data/resolved_bugs/resolved_bugs.json")

    bugs = kb.load_bugs()

    # Create RAG service
    rag = RAGService(bugs)

    query = """
    Login crashes because the user object is null.
    """

    results = rag.find_similar_bugs(query)

    print("\n========== RAG RESULTS ==========")

    for item in results:

        bug = item["bug"]

        print(f"{bug.bug_id} | " f"{bug.title} | " f"{item['similarity']:.2f}")


if __name__ == "__main__":
    main()
