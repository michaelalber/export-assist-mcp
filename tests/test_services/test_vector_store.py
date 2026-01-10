"""Tests for the vector store service."""

from export_control_mcp.models.regulations import RegulationType


class TestVectorStoreService:
    """Tests for VectorStoreService."""

    def test_add_chunk(self, vector_store, embedding_service, sample_ear_chunk):
        """Test adding a single chunk."""
        embedding = embedding_service.embed(sample_ear_chunk.to_embedding_text())
        vector_store.add_chunk(sample_ear_chunk, embedding)

        count = vector_store.count(RegulationType.EAR)
        assert count == 1

    def test_add_chunks_batch(
        self, vector_store, embedding_service, sample_ear_chunk, sample_itar_chunk
    ):
        """Test adding multiple chunks in batch."""
        chunks = [sample_ear_chunk, sample_itar_chunk]
        texts = [c.to_embedding_text() for c in chunks]
        embeddings = embedding_service.embed_batch(texts)

        vector_store.add_chunks_batch(chunks, embeddings)

        assert vector_store.count(RegulationType.EAR) == 1
        assert vector_store.count(RegulationType.ITAR) == 1
        assert vector_store.count() == 2

    def test_search_returns_results(self, populated_vector_store, embedding_service):
        """Test that search returns relevant results."""
        query = "export administration regulations"
        query_embedding = embedding_service.embed(query)

        results = populated_vector_store.search(
            query_embedding=query_embedding,
            limit=5,
        )

        assert len(results) > 0
        # First result should be about EAR since query mentions it
        metadata, score = results[0]
        assert metadata["regulation_type"] == "ear"
        assert score > 0

    def test_search_with_regulation_type_filter(self, populated_vector_store, embedding_service):
        """Test filtering search by regulation type."""
        query = "defense articles export"
        query_embedding = embedding_service.embed(query)

        results = populated_vector_store.search(
            query_embedding=query_embedding,
            regulation_type=RegulationType.ITAR,
            limit=5,
        )

        assert len(results) > 0
        for metadata, _ in results:
            assert metadata["regulation_type"] == "itar"

    def test_get_by_id(self, vector_store, embedding_service, sample_ear_chunk):
        """Test retrieving a chunk by ID."""
        embedding = embedding_service.embed(sample_ear_chunk.to_embedding_text())
        vector_store.add_chunk(sample_ear_chunk, embedding)

        result = vector_store.get_by_id(sample_ear_chunk.id, RegulationType.EAR)

        assert result is not None
        assert result["citation"] == sample_ear_chunk.citation

    def test_get_by_id_not_found(self, vector_store):
        """Test get_by_id returns None for non-existent ID."""
        result = vector_store.get_by_id("nonexistent:id", RegulationType.EAR)
        assert result is None

    def test_delete_all(self, populated_vector_store):
        """Test deleting all chunks."""
        assert populated_vector_store.count() > 0

        populated_vector_store.delete_all()

        assert populated_vector_store.count() == 0

    def test_delete_by_type(self, populated_vector_store):
        """Test deleting chunks by regulation type."""
        assert populated_vector_store.count(RegulationType.EAR) > 0

        populated_vector_store.delete_all(RegulationType.EAR)

        assert populated_vector_store.count(RegulationType.EAR) == 0
        assert populated_vector_store.count(RegulationType.ITAR) > 0
