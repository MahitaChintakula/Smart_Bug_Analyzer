from app.rag.knowledge_base import KnowledgeBase
from app.rag.embeddings import EmbeddingGenerator
from app.rag.vector_store import VectorStore


class RAGService:
    """
    Initializes and manages the RAG pipeline.
    """

    def __init__(self, file_path: str):
        self.knowledge_base = KnowledgeBase(file_path)
        self.embedder = EmbeddingGenerator()

        self.bugs = self.knowledge_base.load_bugs()

        documents = [
            f"{bug.title} {bug.description} {bug.root_cause}" for bug in self.bugs
        ]

        self.embeddings = self.embedder.model.encode(documents)

        self.vector_store = VectorStore(self.embeddings.shape[1])

        self.vector_store.add_embeddings(self.embeddings)

    def search(self, query: str, top_k: int = 3):

        query_embedding = self.embedder.encode(query)

        distances, indices = self.vector_store.search(query_embedding, top_k)

        return distances, indices

    def find_similar_bugs(self, query: str, top_k: int = 3):

        query_embedding = self.embedder.encode(query)

        distances, indices = self.vector_store.search(query_embedding, top_k)

        results = []

        for distance, idx in zip(distances[0], indices[0]):

            similarity = 1 / (1 + float(distance))

            results.append({"bug": self.bugs[idx], "similarity": similarity})

        return results

    def find_similar_bugs(self, query, top_k=3):

        query_embedding = self.embedder.encode(query)

        distances, indices = self.vector_store.search(query_embedding, top_k)

        results = []

        for distance, idx in zip(distances[0], indices[0]):

            similarity = 1 / (1 + float(distance))

            results.append({"bug": self.bugs[idx], "similarity": similarity})

        return results
