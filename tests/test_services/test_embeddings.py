"""Tests for the embedding service."""

import pytest


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    def test_embed_returns_vector(self, embedding_service):
        """Test that embed returns a vector of floats."""
        text = "Export control regulations govern the transfer of technology."
        embedding = embedding_service.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_dimension(self, embedding_service):
        """Test that embedding has correct dimension for model."""
        text = "Test embedding dimension."
        embedding = embedding_service.embed(text)

        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        assert len(embedding) == embedding_service.dimension

    def test_embed_batch(self, embedding_service):
        """Test batch embedding generation."""
        texts = [
            "First text about export controls.",
            "Second text about sanctions.",
            "Third text about ECCN classification.",
        ]
        embeddings = embedding_service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == embedding_service.dimension for e in embeddings)

    def test_embed_batch_empty(self, embedding_service):
        """Test batch embedding with empty list."""
        embeddings = embedding_service.embed_batch([])
        assert embeddings == []

    def test_similar_texts_have_similar_embeddings(self, embedding_service):
        """Test that semantically similar texts produce similar embeddings."""
        import numpy as np

        text1 = "Export control regulations for dual-use items."
        text2 = "Export restrictions for dual-use goods."
        text3 = "The weather is nice today."

        emb1 = np.array(embedding_service.embed(text1))
        emb2 = np.array(embedding_service.embed(text2))
        emb3 = np.array(embedding_service.embed(text3))

        # Cosine similarity
        sim_12 = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        sim_13 = np.dot(emb1, emb3) / (np.linalg.norm(emb1) * np.linalg.norm(emb3))

        # Similar texts should have higher similarity
        assert sim_12 > sim_13
