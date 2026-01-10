"""RAG (Retrieval-Augmented Generation) service for regulation search."""

from export_control_mcp.models.errors import RegulationNotFoundError
from export_control_mcp.models.regulations import (
    RegulationChunk,
    RegulationType,
    SearchResult,
)
from export_control_mcp.services.embeddings import EmbeddingService
from export_control_mcp.services.vector_store import VectorStoreService


class RagService:
    """Retrieval-Augmented Generation service for export control regulations."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStoreService,
    ):
        """
        Initialize the RAG service.

        Args:
            embedding_service: Service for generating query embeddings.
            vector_store: Service for vector similarity search.
        """
        self._embeddings = embedding_service
        self._vector_store = vector_store

    async def search(
        self,
        query: str,
        regulation_type: RegulationType | None = None,
        part: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Semantic search for export control regulations.

        Args:
            query: Natural language search query.
            regulation_type: Optional filter (EAR or ITAR). None searches all.
            part: Optional part filter (e.g., "Part 730").
            limit: Maximum number of results to return.

        Returns:
            Ranked list of regulation chunks with relevance scores.
        """
        # Generate query embedding
        query_embedding = self._embeddings.embed(query)

        # Search vector store
        results = self._vector_store.search(
            query_embedding=query_embedding,
            regulation_type=regulation_type,
            part=part,
            limit=limit,
        )

        # Convert to SearchResult objects
        search_results: list[SearchResult] = []
        for metadata, score in results:
            # Reconstruct RegulationChunk from stored JSON
            full_json = metadata.get("full_json")
            if full_json:
                chunk = RegulationChunk.model_validate_json(full_json)
                search_results.append(
                    SearchResult(
                        chunk=chunk,
                        score=score,
                    )
                )

        return search_results

    async def search_ear(
        self,
        query: str,
        part: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Search Export Administration Regulations (EAR) only.

        Args:
            query: Natural language search query.
            part: Optional part filter (e.g., "Part 730").
            limit: Maximum number of results.

        Returns:
            Ranked list of EAR regulation chunks.
        """
        return await self.search(
            query=query,
            regulation_type=RegulationType.EAR,
            part=part,
            limit=limit,
        )

    async def search_itar(
        self,
        query: str,
        part: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Search International Traffic in Arms Regulations (ITAR) only.

        Args:
            query: Natural language search query.
            part: Optional part filter (e.g., "Part 120").
            limit: Maximum number of results.

        Returns:
            Ranked list of ITAR regulation chunks.
        """
        return await self.search(
            query=query,
            regulation_type=RegulationType.ITAR,
            part=part,
            limit=limit,
        )

    async def get_chunk(
        self,
        chunk_id: str,
        regulation_type: RegulationType,
    ) -> RegulationChunk:
        """
        Retrieve a specific regulation chunk by ID.

        Args:
            chunk_id: Chunk identifier.
            regulation_type: EAR or ITAR.

        Returns:
            The requested regulation chunk.

        Raises:
            RegulationNotFoundError: If the chunk doesn't exist.
        """
        metadata = self._vector_store.get_by_id(chunk_id, regulation_type)

        if metadata is None:
            raise RegulationNotFoundError(chunk_id, regulation_type.value)

        full_json = metadata.get("full_json")
        if not full_json:
            raise RegulationNotFoundError(chunk_id, regulation_type.value)

        return RegulationChunk.model_validate_json(full_json)

    def get_store_count(self, regulation_type: RegulationType | None = None) -> int:
        """Return the number of chunks in the vector store."""
        return self._vector_store.count(regulation_type)
