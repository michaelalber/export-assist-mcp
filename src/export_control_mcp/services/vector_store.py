"""Vector store service using ChromaDB."""

from typing import Any

import chromadb
from chromadb import ClientAPI, Collection

from export_control_mcp.models.errors import VectorStoreError
from export_control_mcp.models.regulations import RegulationChunk, RegulationType


class VectorStoreService:
    """ChromaDB wrapper for export control regulation storage and retrieval."""

    # Collection names for different regulation types
    EAR_COLLECTION = "ear_regulations"
    ITAR_COLLECTION = "itar_regulations"

    def __init__(self, db_path: str):
        """
        Initialize ChromaDB in persistent mode.

        Args:
            db_path: Path to the ChromaDB storage directory.
        """
        self._db_path = db_path
        self._client: ClientAPI | None = None
        self._collections: dict[str, Collection] = {}

    @property
    def client(self) -> ClientAPI:
        """Lazy-load and return the ChromaDB client."""
        if self._client is None:
            try:
                self._client = chromadb.PersistentClient(path=self._db_path)
            except Exception as e:
                raise VectorStoreError(
                    f"Failed to initialize ChromaDB at '{self._db_path}': {e}"
                ) from e
        return self._client

    def _get_collection(self, regulation_type: RegulationType) -> Collection:
        """Get or create a collection for the given regulation type."""
        collection_name = (
            self.EAR_COLLECTION if regulation_type == RegulationType.EAR else self.ITAR_COLLECTION
        )

        if collection_name not in self._collections:
            try:
                self._collections[collection_name] = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                raise VectorStoreError(
                    f"Failed to access collection '{collection_name}': {e}"
                ) from e

        return self._collections[collection_name]

    def add_chunk(self, chunk: RegulationChunk, embedding: list[float]) -> None:
        """
        Add a single regulation chunk with its embedding.

        Args:
            chunk: The regulation chunk to store.
            embedding: Pre-computed embedding vector.

        Raises:
            VectorStoreError: If the operation fails.
        """
        collection = self._get_collection(chunk.regulation_type)

        try:
            collection.add(
                ids=[chunk.id],
                embeddings=[embedding],
                documents=[chunk.content],
                metadatas=[
                    {
                        "regulation_type": chunk.regulation_type.value,
                        "part": chunk.part,
                        "section": chunk.section or "",
                        "title": chunk.title,
                        "citation": chunk.citation,
                        "chunk_index": chunk.chunk_index,
                        "full_json": chunk.model_dump_json(),
                    }
                ],
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to add chunk '{chunk.id}': {e}") from e

    def add_chunks_batch(
        self,
        chunks: list[RegulationChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Add multiple regulation chunks efficiently.

        Args:
            chunks: List of chunks to store.
            embeddings: Corresponding embedding vectors.

        Raises:
            VectorStoreError: If the operation fails.
            ValueError: If chunks and embeddings lengths don't match.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have same length"
            )

        if not chunks:
            return

        # Group chunks by regulation type
        by_type: dict[RegulationType, tuple[list[RegulationChunk], list[list[float]]]] = {}
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            if chunk.regulation_type not in by_type:
                by_type[chunk.regulation_type] = ([], [])
            by_type[chunk.regulation_type][0].append(chunk)
            by_type[chunk.regulation_type][1].append(embedding)

        # Add each group to its collection
        for reg_type, (type_chunks, type_embeddings) in by_type.items():
            collection = self._get_collection(reg_type)
            try:
                collection.add(
                    ids=[c.id for c in type_chunks],
                    embeddings=type_embeddings,
                    documents=[c.content for c in type_chunks],
                    metadatas=[
                        {
                            "regulation_type": c.regulation_type.value,
                            "part": c.part,
                            "section": c.section or "",
                            "title": c.title,
                            "citation": c.citation,
                            "chunk_index": c.chunk_index,
                            "full_json": c.model_dump_json(),
                        }
                        for c in type_chunks
                    ],
                )
            except Exception as e:
                raise VectorStoreError(
                    f"Failed to add batch of {len(type_chunks)} chunks: {e}"
                ) from e

    def search(
        self,
        query_embedding: list[float],
        regulation_type: RegulationType | None = None,
        part: str | None = None,
        limit: int = 10,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Search for similar regulation chunks.

        Args:
            query_embedding: Query vector.
            regulation_type: Optional regulation type filter (EAR or ITAR).
            part: Optional part filter (e.g., "Part 730").
            limit: Maximum number of results.

        Returns:
            List of (metadata, score) tuples, where score is similarity (0-1).

        Raises:
            VectorStoreError: If the search fails.
        """
        # Determine which collections to search
        if regulation_type:
            collections = [self._get_collection(regulation_type)]
        else:
            collections = [
                self._get_collection(RegulationType.EAR),
                self._get_collection(RegulationType.ITAR),
            ]

        all_results: list[tuple[dict[str, Any], float]] = []

        for collection in collections:
            try:
                where = {"part": part} if part else None
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where,
                    include=["metadatas", "distances"],
                )

                if results["metadatas"] and results["distances"]:
                    for metadata, distance in zip(
                        results["metadatas"][0],
                        results["distances"][0],
                        strict=True,
                    ):
                        # Cosine distance to similarity: similarity = 1 - distance
                        similarity = max(0.0, 1.0 - distance)
                        all_results.append((metadata, similarity))

            except Exception as e:
                raise VectorStoreError(f"Search failed: {e}") from e

        # Sort by score and return top results
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:limit]

    def get_by_id(self, chunk_id: str, regulation_type: RegulationType) -> dict[str, Any] | None:
        """
        Get a chunk by exact ID match.

        Args:
            chunk_id: Chunk identifier.
            regulation_type: The regulation type to search in.

        Returns:
            Chunk metadata dict or None if not found.

        Raises:
            VectorStoreError: If the operation fails.
        """
        collection = self._get_collection(regulation_type)

        try:
            results = collection.get(
                ids=[chunk_id],
                include=["metadatas"],
            )
            if results["metadatas"]:
                return results["metadatas"][0]
            return None

        except Exception as e:
            raise VectorStoreError(f"Failed to get chunk '{chunk_id}': {e}") from e

    def count(self, regulation_type: RegulationType | None = None) -> int:
        """
        Return the total number of chunks in the store.

        Args:
            regulation_type: Optional type to count. None counts all.

        Returns:
            Number of stored chunks.
        """
        if regulation_type:
            return self._get_collection(regulation_type).count()

        total = 0
        for reg_type in RegulationType:
            try:
                total += self._get_collection(reg_type).count()
            except Exception:
                pass  # Collection may not exist yet
        return total

    def delete_all(self, regulation_type: RegulationType | None = None) -> None:
        """
        Delete all chunks from the collection(s).

        Args:
            regulation_type: Optional type to delete. None deletes all.

        Warning: Use with caution.
        """
        types = [regulation_type] if regulation_type else list(RegulationType)

        for reg_type in types:
            try:
                collection = self._get_collection(reg_type)
                all_ids = collection.get()["ids"]
                if all_ids:
                    collection.delete(ids=all_ids)
            except Exception as e:
                raise VectorStoreError(f"Failed to delete chunks: {e}") from e
