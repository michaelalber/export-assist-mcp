"""Base classes for data ingestion."""

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field

from export_control_mcp.models.regulations import RegulationType
from export_control_mcp.services.embeddings import EmbeddingService
from export_control_mcp.services.vector_store import VectorStoreService


class IngestResult(BaseModel):
    """Result of an ingestion operation."""

    regulation_type: str = Field(..., description="Regulation type ingested (ear/itar)")
    sections_ingested: int = Field(default=0, description="Number of sections processed")
    chunks_created: int = Field(default=0, description="Total text chunks created")
    errors: list[str] = Field(default_factory=list, description="Error messages")

    @property
    def success(self) -> bool:
        """Check if ingestion was successful (at least some content ingested)."""
        return self.chunks_created > 0


class BaseIngestor(ABC):
    """Abstract base class for regulation ingestors."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStoreService,
        batch_size: int = 50,
    ):
        """
        Initialize the ingestor.

        Args:
            embedding_service: Service for generating embeddings.
            vector_store: Service for storing regulation chunks.
            batch_size: Number of chunks to process per batch.
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.batch_size = batch_size

    @property
    @abstractmethod
    def regulation_type(self) -> RegulationType:
        """Return the regulation type being ingested (EAR or ITAR)."""
        ...

    @property
    def regulation_name(self) -> str:
        """Return human-readable name for the regulation type."""
        return "EAR" if self.regulation_type == RegulationType.EAR else "ITAR"

    @abstractmethod
    async def ingest(self, source_path: Path) -> IngestResult:
        """
        Ingest regulation data from the source into the vector store.

        Args:
            source_path: Path to the source data (file or directory).

        Returns:
            IngestResult with statistics and any errors.
        """
        ...

    def _create_result(self) -> IngestResult:
        """Create a new IngestResult for this regulation type."""
        return IngestResult(regulation_type=self.regulation_type.value)
