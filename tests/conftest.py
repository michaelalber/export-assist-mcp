"""Pytest fixtures for export control MCP tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def embedding_service():
    """
    Shared embedding service instance.

    Scope is session-wide because loading the embedding model is slow.
    """
    from export_control_mcp.services.embeddings import EmbeddingService

    return EmbeddingService(model_name="all-MiniLM-L6-v2")


@pytest.fixture
def temp_chroma_path():
    """Temporary ChromaDB path for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "chroma"


@pytest.fixture
def temp_audit_log():
    """Temporary audit log file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def vector_store(temp_chroma_path):
    """Vector store with temporary storage."""
    from export_control_mcp.services.vector_store import VectorStoreService

    return VectorStoreService(db_path=str(temp_chroma_path))


@pytest.fixture
def rag_service(embedding_service, vector_store):
    """RAG service with test dependencies."""
    from export_control_mcp.services.rag import RagService

    return RagService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


@pytest.fixture
def sample_ear_chunk():
    """Sample EAR regulation chunk for testing."""
    from export_control_mcp.models.regulations import RegulationChunk, RegulationType

    return RegulationChunk(
        id="ear:part-730:730.1:chunk-000",
        regulation_type=RegulationType.EAR,
        part="Part 730",
        section="730.1",
        title="Scope",
        content="""The Export Administration Regulations (EAR) are issued by the
        United States Department of Commerce, Bureau of Industry and Security (BIS),
        under the Export Control Reform Act of 2018 (ECRA). The EAR regulate the
        export, reexport, and transfer (in-country) of items, including commodities,
        software, and technology. The term 'export' includes the actual shipment or
        transmission of items out of the United States, as well as releasing or
        otherwise transferring technology or source code to a foreign national in
        the United States (deemed export).""",
        citation="15 CFR 730.1",
        chunk_index=0,
    )


@pytest.fixture
def sample_itar_chunk():
    """Sample ITAR regulation chunk for testing."""
    from export_control_mcp.models.regulations import RegulationChunk, RegulationType

    return RegulationChunk(
        id="itar:part-120:120.1:chunk-000",
        regulation_type=RegulationType.ITAR,
        part="Part 120",
        section="120.1",
        title="General Authorities, Eligibility, and Information",
        content="""The Arms Export Control Act and Executive Order 13637 authorize
        the President to control the export and import of defense articles and
        defense services. The statutory authority of the President to promulgate
        regulations with respect to exports of defense articles and defense services
        is delegated to the Secretary of State. The International Traffic in Arms
        Regulations (ITAR) implement the Arms Export Control Act and are subject
        to Executive Order 13637.""",
        citation="22 CFR 120.1",
        chunk_index=0,
    )


@pytest.fixture
def populated_vector_store(vector_store, embedding_service, sample_ear_chunk, sample_itar_chunk):
    """Vector store pre-populated with sample chunks."""
    chunks = [sample_ear_chunk, sample_itar_chunk]

    texts = [chunk.to_embedding_text() for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)

    vector_store.add_chunks_batch(chunks, embeddings)

    return vector_store
