from app.rag.embeddings import EmbeddingGenerator
from app.rag.vector_store import VectorStore


class RAGService:
    """
    Connects the knowledge base, embedding generator,
    and FAISS vector store.
    """

    def __init__(self, bugs):

        self.bugs = bugs

        # Create embedding generator
        self.embedding_generator = EmbeddingGenerator()

        # all-MiniLM-L6-v2 produces 384-dimensional vectors
        self.vector_store = VectorStore(dimension=384)

        # Create embeddings for historical bugs
        embeddings = []

        for bug in self.bugs:

            text = self._bug_to_text(bug)

            embedding = self.embedding_generator.encode(text)

            embeddings.append(embedding)

        # Add all historical bug embeddings to FAISS
        if embeddings:
            self.vector_store.add_embeddings(embeddings)

    def _bug_to_text(self, bug):

        return f"""
Title: {bug.title}

Description: {getattr(bug, "description", "")}

Severity: {getattr(bug, "severity", "")}

Priority: {getattr(bug, "priority", "")}

Module: {getattr(bug, "module", "")}

Exception: {getattr(bug, "exception", "")}

Stack Trace: {getattr(bug, "stack_trace", "")}

Root Cause: {getattr(bug, "root_cause", "")}

Resolution: {getattr(bug, "resolution", "")}
"""

    def find_similar_bugs(self, query, k=3):

        if not self.bugs:
            return []

        # Convert new bug report into embedding
        query_embedding = self.embedding_generator.encode(query)

        # Search FAISS
        distances, indices = self.vector_store.search(
            query_embedding, k=min(k, len(self.bugs))
        )

        results = []

        for distance, index in zip(distances[0], indices[0]):

            # Ignore invalid FAISS results
            if index < 0:
                continue

            bug = self.bugs[index]

            # Convert distance into similarity score
            similarity = 1 / (1 + float(distance))

            results.append({"bug": bug, "similarity": similarity})

        return results

    def add_bug(self, bug) -> bool:
        """Add a newly persisted bug to the live FAISS index."""
        if any(existing.bug_id == bug.bug_id for existing in self.bugs):
            return False

        embedding = self.embedding_generator.encode(self._bug_to_text(bug))
        self.vector_store.add_embeddings([embedding])
        self.bugs.append(bug)

        return True
