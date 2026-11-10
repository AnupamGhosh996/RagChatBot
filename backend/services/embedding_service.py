import numpy as np
from typing import List
from backend.config import settings

class EmbeddingService:
    """
    Generates dense vector embeddings using Hugging Face's
    Sentence Transformers model ('all-MiniLM-L6-v2').
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Loads model onto CPU or GPU if available
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load embedding model '{self.model_name}'. "
                    f"Ensure 'sentence-transformers' and 'torch' are installed. Error: {e}"
                )
        return self._model

    @property
    def embedding_dimension(self) -> int:
        """all-MiniLM-L6-v2 produces 384-dimensional dense vectors."""
        return 384

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embeds a list of texts into a 2D float32 numpy array [N, dimension].
        L2-normalizes vectors so that dot product equals cosine similarity.
        """
        if not texts:
            return np.empty((0, self.embedding_dimension), dtype=np.float32)

        model = self._load_model()
        # normalize_embeddings=True calculates unit vectors directly
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embeds a single search query string into a 1D float32 normalized vector.
        """
        embeddings = self.embed_texts([query])
        return embeddings[0]

# Singleton instance
embedding_service = EmbeddingService()
