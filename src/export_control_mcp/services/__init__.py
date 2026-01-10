"""Service layer with singleton getters.

Uses @lru_cache for lazy singleton pattern to avoid circular imports
and enable late binding of dependencies.
"""

from functools import lru_cache
from typing import TYPE_CHECKING

from export_control_mcp.config import settings

if TYPE_CHECKING:
    from export_control_mcp.services.embeddings import EmbeddingService
    from export_control_mcp.services.vector_store import VectorStoreService
    from export_control_mcp.services.rag import RagService


@lru_cache(maxsize=1)
def get_embedding_service() -> "EmbeddingService":
    """Get singleton embedding service instance."""
    from export_control_mcp.services.embeddings import EmbeddingService

    return EmbeddingService(model_name=settings.embedding_model)


@lru_cache(maxsize=1)
def get_vector_store() -> "VectorStoreService":
    """Get singleton vector store service instance."""
    from export_control_mcp.services.vector_store import VectorStoreService

    return VectorStoreService(db_path=settings.chroma_persist_dir)


@lru_cache(maxsize=1)
def get_rag_service() -> "RagService":
    """Get singleton RAG service instance."""
    from export_control_mcp.services.rag import RagService

    return RagService(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
    )


__all__ = [
    "get_embedding_service",
    "get_vector_store",
    "get_rag_service",
]
