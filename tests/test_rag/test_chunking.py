"""Tests for regulation text chunking."""

import pytest

from export_control_mcp.models.regulations import RegulationType
from export_control_mcp.rag.chunking import ChunkMetadata, RegulationChunker


class TestRegulationChunker:
    """Tests for RegulationChunker."""

    @pytest.fixture
    def chunker(self):
        """Create a chunker with small max_tokens for testing."""
        return RegulationChunker(max_tokens=100, overlap_tokens=10)

    def test_short_text_single_chunk(self, chunker):
        """Test that short text produces a single chunk."""
        text = "This is a short regulation text."
        metadata = ChunkMetadata(
            part="Part 730",
            section="730.1",
            title="Scope",
            citation="15 CFR 730.1",
        )

        chunks = chunker.chunk_text(text, metadata, RegulationType.EAR)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].part == "Part 730"
        assert chunks[0].section == "730.1"

    def test_long_text_multiple_chunks(self, chunker):
        """Test that long text is split into multiple chunks."""
        # Generate text longer than max_tokens (100 tokens)
        # Each sentence is ~20 tokens, so 10 sentences should exceed 100 tokens
        sentences = [
            "The Export Administration Regulations govern the export of dual-use items from the United States.",
            "These regulations are administered by the Bureau of Industry and Security within the Department of Commerce.",
            "Items subject to the EAR include commercial products that could have military applications.",
            "A license may be required depending on the item classification and destination country.",
            "License exceptions provide alternatives to obtaining a license for certain exports.",
            "The Commerce Control List contains all items subject to export controls under the EAR.",
            "End-use and end-user restrictions may apply even to items not otherwise controlled.",
            "Deemed exports occur when technology is released to foreign nationals in the United States.",
            "Reexports from third countries are also subject to EAR jurisdiction in many cases.",
            "Violations of the EAR can result in significant civil and criminal penalties.",
        ]
        text = " ".join(sentences)
        metadata = ChunkMetadata(
            part="Part 730",
            title="Scope",
            citation="15 CFR 730",
        )

        chunks = chunker.chunk_text(text, metadata, RegulationType.EAR)

        assert len(chunks) > 1
        # All chunks should have same part
        assert all(c.part == "Part 730" for c in chunks)
        # Chunk indices should be sequential
        assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

    def test_chunk_id_format(self, chunker):
        """Test that chunk IDs have correct format."""
        text = "Short text for ID test."
        metadata = ChunkMetadata(
            part="Part 742",
            section="742.4",
            title="Control Policy",
            citation="15 CFR 742.4",
        )

        chunks = chunker.chunk_text(text, metadata, RegulationType.EAR)

        assert len(chunks) == 1
        # ID should be: ear:part-742:742.4:chunk-000
        assert chunks[0].id.startswith("ear:part-742:742.4:chunk-")

    def test_count_tokens(self, chunker):
        """Test token counting."""
        text = "Hello world"
        count = chunker.count_tokens(text)

        assert count > 0
        assert isinstance(count, int)

    def test_paragraph_preservation(self, chunker):
        """Test that chunking respects paragraph boundaries when possible."""
        text = "First paragraph about exports.\n\nSecond paragraph about controls.\n\nThird paragraph about licensing."
        metadata = ChunkMetadata(
            part="Part 750",
            title="Applications",
            citation="15 CFR 750",
        )

        chunks = chunker.chunk_text(text, metadata, RegulationType.EAR)

        # Content should not have broken mid-sentence
        for chunk in chunks:
            # Check no broken sentences (simple heuristic)
            assert not chunk.content.endswith(",")

    def test_regulation_type_in_chunk(self, chunker):
        """Test that regulation type is correctly set in chunks."""
        text = "Test content."
        metadata = ChunkMetadata(part="Part 121", title="USML", citation="22 CFR 121")

        ear_chunks = chunker.chunk_text(text, metadata, RegulationType.EAR)
        itar_chunks = chunker.chunk_text(text, metadata, RegulationType.ITAR)

        assert ear_chunks[0].regulation_type == RegulationType.EAR
        assert itar_chunks[0].regulation_type == RegulationType.ITAR
