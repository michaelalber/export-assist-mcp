"""Embedding service using sentence-transformers."""

from sentence_transformers import SentenceTransformer

from export_control_mcp.models.errors import EmbeddingError


class EmbeddingService:
    """Generate embeddings using sentence-transformers models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service.

        The model is loaded lazily on first use to avoid startup delay.

        Args:
            model_name: Name of the sentence-transformers model to use.
                        Default is all-MiniLM-L6-v2 (384 dimensions, fast).
                        Alternative: BAAI/bge-small-en-v1.5 (better quality).
        """
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load and return the model."""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self._model_name)
            except Exception as e:
                raise EmbeddingError(f"Failed to load model '{self._model_name}': {e}") from e
        return self._model

    @property
    def dimension(self) -> int:
        """Return the embedding dimension for this model."""
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed.
            batch_size: Number of texts to process at once.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not texts:
            return []

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100,
            )
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e
