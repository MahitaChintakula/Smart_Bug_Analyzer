# from app.models.search_result import SearchResult


# class DuplicateDetectionAgent:
#     """
#     Detects similar historical bugs using semantic search.
#     """

#     def __init__(self, knowledge_base, embedder, vector_store):
#         self.knowledge_base = knowledge_base
#         self.embedder = embedder
#         self.vector_store = vector_store

#     def find_duplicates(self, query: str, top_k: int = 3):
#         bugs = self.knowledge_base.load_bugs()

#         query_embedding = self.embedder.encode(query)

#         distances, indices = self.vector_store.search(query_embedding, top_k)

#         results = []

#         for distance, index in zip(distances[0], indices[0]):
#             bug = bugs[index]

#             similarity = 1 / (1 + float(distance))

#             results.append(
#                 SearchResult(
#                     bug_id=bug.bug_id,
#                     title=bug.title,
#                     severity=bug.severity,
#                     priority=bug.priority,
#                     similarity_score=round(similarity, 3)
#                 )
#             )

#         return results

from app.models.search_result import SearchResult


class DuplicateDetectionAgent:

    def __init__(self, rag_service):
        self.rag_service = rag_service

    def analyze(self, query):

        matches = self.rag_service.find_similar_bugs(query)

        results = []

        for item in matches:

            bug = item["bug"]

            results.append(
                SearchResult(
                    bug_id=bug.bug_id,
                    title=bug.title,
                    severity=bug.severity,
                    priority=bug.priority,
                    similarity_score=round(item["similarity"], 2),
                )
            )

        return results
