import faiss
import numpy as np


class VectorStore:
    """
    Handles FAISS vector indexing and similarity search.
    """

    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatL2(dimension)

    def add_embeddings(self, embeddings):
        """
        Add embeddings to the FAISS index.
        """
        embeddings = np.array(embeddings).astype("float32")
        self.index.add(embeddings)

    def search(self, query_embedding, k=3):
        """
        Search for the k most similar embeddings.
        """
        query_embedding = np.array([query_embedding]).astype("float32")

        distances, indices = self.index.search(query_embedding, k)

        return distances, indices
