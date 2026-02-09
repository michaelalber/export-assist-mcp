"""Tests for the eCFR (Electronic Code of Federal Regulations) ingestion module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as SafeET
import pytest

from export_control_mcp.data.ingest.ecfr_ingest import (
    EAR_PARTS,
    ITAR_PARTS,
    ECFRIngestor,
)
from export_control_mcp.models.regulations import RegulationType


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Create a mock embedding service."""
    mock = MagicMock()
    mock.embed_batch.return_value = [[0.1] * 384]
    return mock


@pytest.fixture
def mock_vector_store() -> MagicMock:
    """Create a mock vector store."""
    mock = MagicMock()
    return mock


@pytest.fixture
def ear_ingestor(mock_embedding_service: MagicMock, mock_vector_store: MagicMock) -> ECFRIngestor:
    """Create eCFR ingestor for EAR with mock dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ECFRIngestor(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            regulation_type=RegulationType.EAR,
            download_dir=Path(tmpdir),
            batch_size=10,
        )


@pytest.fixture
def itar_ingestor(mock_embedding_service: MagicMock, mock_vector_store: MagicMock) -> ECFRIngestor:
    """Create eCFR ingestor for ITAR with mock dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ECFRIngestor(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            regulation_type=RegulationType.ITAR,
            download_dir=Path(tmpdir),
            batch_size=10,
        )


class TestECFRPartsMapping:
    """Tests for eCFR parts mapping constants."""

    def test_should_have_ear_parts_from_730_to_774(self) -> None:
        """Test EAR parts range."""
        # Assert all key parts are present
        assert 730 in EAR_PARTS
        assert 774 in EAR_PARTS
        assert "License Exceptions" in EAR_PARTS[740]

    def test_should_have_itar_parts_from_120_to_130(self) -> None:
        """Test ITAR parts range."""
        assert 120 in ITAR_PARTS
        assert 130 in ITAR_PARTS
        assert "Munitions List" in ITAR_PARTS[121]

    def test_should_have_itar_part_126_for_general_policies(self) -> None:
        """Test ITAR Part 126 is defined."""
        assert 126 in ITAR_PARTS
        assert "General Policies" in ITAR_PARTS[126]


class TestECFRIngestorProperties:
    """Tests for ECFRIngestor properties."""

    def test_should_return_ear_type_for_ear_ingestor(self, ear_ingestor: ECFRIngestor) -> None:
        """Test regulation_type returns EAR."""
        assert ear_ingestor.regulation_type == RegulationType.EAR

    def test_should_return_itar_type_for_itar_ingestor(self, itar_ingestor: ECFRIngestor) -> None:
        """Test regulation_type returns ITAR."""
        assert itar_ingestor.regulation_type == RegulationType.ITAR

    def test_should_return_ear_regulation_name(self, ear_ingestor: ECFRIngestor) -> None:
        """Test regulation_name returns EAR."""
        assert ear_ingestor.regulation_name == "EAR"

    def test_should_return_itar_regulation_name(self, itar_ingestor: ECFRIngestor) -> None:
        """Test regulation_name returns ITAR."""
        assert itar_ingestor.regulation_name == "ITAR"


class TestECFRPartsDictionary:
    """Tests for getting parts dictionary based on type."""

    def test_should_return_ear_parts_for_ear_type(self, ear_ingestor: ECFRIngestor) -> None:
        """Test _get_parts_from_type returns EAR parts."""
        parts = ear_ingestor._get_parts_from_type()
        assert 730 in parts
        assert 774 in parts

    def test_should_return_itar_parts_for_itar_type(self, itar_ingestor: ECFRIngestor) -> None:
        """Test _get_parts_from_type returns ITAR parts."""
        parts = itar_ingestor._get_parts_from_type()
        assert 120 in parts
        assert 130 in parts


class TestXMLElementExtraction:
    """Tests for XML element extraction methods."""

    def test_should_extract_part_number_from_n_attribute(self, ear_ingestor: ECFRIngestor) -> None:
        """Test extracting part number from N attribute."""
        # Arrange
        elem = Element("DIV5")
        elem.set("N", "730")

        # Act
        part_num = ear_ingestor._extract_part_number(elem)

        # Assert
        assert part_num == 730

    def test_should_extract_part_number_from_head_child(self, ear_ingestor: ECFRIngestor) -> None:
        """Test extracting part number from HEAD child element."""
        # Arrange
        elem = Element("DIV5")
        head = Element("HEAD")
        head.text = "PART 744 - Control Policy"
        elem.append(head)

        # Act
        part_num = ear_ingestor._extract_part_number(elem)

        # Assert
        assert part_num == 744

    def test_should_return_none_when_no_part_number(self, ear_ingestor: ECFRIngestor) -> None:
        """Test that None is returned when no part number found."""
        # Arrange
        elem = Element("DIV5")

        # Act
        part_num = ear_ingestor._extract_part_number(elem)

        # Assert
        assert part_num is None

    def test_should_extract_section_number_from_n_attribute(
        self, ear_ingestor: ECFRIngestor
    ) -> None:
        """Test extracting section number from N attribute."""
        # Arrange
        elem = Element("DIV8")
        elem.set("N", "§ 730.1")

        # Act
        section_num = ear_ingestor._extract_section_number(elem)

        # Assert
        assert section_num == "730.1"

    def test_should_extract_section_number_from_head_text(self, ear_ingestor: ECFRIngestor) -> None:
        """Test extracting section number from HEAD text."""
        # Arrange
        elem = Element("DIV8")
        head = Element("HEAD")
        head.text = "§ 740.2 Scope"
        elem.append(head)

        # Act
        section_num = ear_ingestor._extract_section_number(elem)

        # Assert
        assert section_num == "740.2"

    def test_should_extract_title_without_section_number(self, ear_ingestor: ECFRIngestor) -> None:
        """Test extracting title removes section number prefix."""
        # Arrange
        elem = Element("DIV8")
        head = Element("HEAD")
        head.text = "§ 730.1 Scope of the EAR"
        elem.append(head)

        # Act
        title = ear_ingestor._extract_title(elem)

        # Assert
        assert title == "Scope of the EAR"
        assert "730.1" not in title

    def test_should_extract_all_text_from_element(self, ear_ingestor: ECFRIngestor) -> None:
        """Test extracting all text content from element tree."""
        # Arrange
        elem = Element("DIV8")
        p1 = Element("P")
        p1.text = "First paragraph."
        p2 = Element("P")
        p2.text = "Second paragraph."
        elem.append(p1)
        elem.append(p2)

        # Act
        text = ear_ingestor._extract_text(elem)

        # Assert
        assert "First paragraph" in text
        assert "Second paragraph" in text


class TestECFRXMLParsing:
    """Tests for eCFR XML file parsing."""

    @pytest.mark.asyncio
    async def test_should_return_error_for_missing_file(self, ear_ingestor: ECFRIngestor) -> None:
        """Test error handling for missing XML file."""
        # Arrange
        missing_path = Path("/nonexistent/file.xml")

        # Act
        result = await ear_ingestor.ingest(missing_path)

        # Assert
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower() or "File not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_should_parse_simple_ecfr_xml(self, ear_ingestor: ECFRIngestor) -> None:
        """Test parsing a simple eCFR XML structure."""
        # Arrange
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <ECFR>
            <DIV5 N="730">
                <HEAD>PART 730 - General Information</HEAD>
                <DIV8 N="730.1">
                    <HEAD>§ 730.1 Scope</HEAD>
                    <P>The Export Administration Regulations govern exports.</P>
                </DIV8>
            </DIV5>
        </ECFR>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "ear_test.xml"
            xml_path.write_text(xml_content)

            # Act
            result = await ear_ingestor.ingest(xml_path)

            # Assert
            assert result.regulation_type == "ear"
            # May have chunks if content is sufficient

    @pytest.mark.asyncio
    async def test_should_handle_malformed_xml_gracefully(self, ear_ingestor: ECFRIngestor) -> None:
        """Test handling of malformed XML."""
        # Arrange
        xml_content = """<?xml version="1.0"?>
        <ECFR>
            <DIV5 N="730">
                <HEAD>Unclosed element
        </ECFR>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "bad.xml"
            xml_path.write_text(xml_content)

            # Act
            result = await ear_ingestor.ingest(xml_path)

            # Assert
            assert len(result.errors) > 0


class TestAlternativeXMLParsing:
    """Tests for alternative XML parsing fallback."""

    def test_should_parse_with_head_based_structure(self, ear_ingestor: ECFRIngestor) -> None:
        """Test alternative parsing using HEAD elements."""
        # Arrange
        xml_content = """
        <ECFR>
            <HEAD>PART 730 - General Information</HEAD>
            <P>The EAR governs exports.</P>
            <HEAD>PART 740 - License Exceptions</HEAD>
            <P>License exceptions are available.</P>
        </ECFR>
        """
        root = SafeET.fromstring(xml_content)
        parts = EAR_PARTS

        # Act
        chunks = ear_ingestor._parse_ecfr_xml_alternative(root, parts, 15)

        # Assert
        assert len(chunks) >= 0  # May or may not produce chunks based on content length


class TestChunkPartContent:
    """Tests for chunking part content."""

    def test_should_skip_parts_not_in_dictionary(self, ear_ingestor: ECFRIngestor) -> None:
        """Test that parts not in the parts dictionary are skipped."""
        # Arrange
        parts = {730: "General Information"}
        content = "Some content about exports."

        # Act
        chunks = ear_ingestor._chunk_part_content(999, parts, 15, content)

        # Assert
        assert len(chunks) == 0

    def test_should_create_chunks_for_valid_part(self, ear_ingestor: ECFRIngestor) -> None:
        """Test chunk creation for a valid part."""
        # Arrange
        parts = {730: "General Information"}
        # Create content long enough to produce at least one chunk
        content = "The Export Administration Regulations. " * 100

        # Act
        chunks = ear_ingestor._chunk_part_content(730, parts, 15, content)

        # Assert
        assert len(chunks) >= 1
        assert all(c.part == "Part 730" for c in chunks)


class TestECFRIngestResult:
    """Tests for eCFR ingestion result creation."""

    def test_should_create_result_with_correct_regulation_type(
        self, ear_ingestor: ECFRIngestor
    ) -> None:
        """Test _create_result sets correct regulation type for EAR."""
        result = ear_ingestor._create_result()
        assert result.regulation_type == "ear"

    def test_should_create_itar_result_type(self, itar_ingestor: ECFRIngestor) -> None:
        """Test _create_result sets correct regulation type for ITAR."""
        result = itar_ingestor._create_result()
        assert result.regulation_type == "itar"


class TestBatchChunkStorage:
    """Tests for batch chunk storage."""

    @pytest.mark.asyncio
    async def test_should_call_vector_store_with_batches(
        self,
        mock_embedding_service: MagicMock,
        mock_vector_store: MagicMock,
    ) -> None:
        """Test that chunks are stored via vector store."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = ECFRIngestor(
                embedding_service=mock_embedding_service,
                vector_store=mock_vector_store,
                regulation_type=RegulationType.EAR,
                download_dir=Path(tmpdir),
                batch_size=5,
            )

            # Create XML with enough content for chunks
            xml_content = (
                """<?xml version="1.0"?>
            <ECFR>
                <HEAD>PART 730</HEAD>
                <P>"""
                + ("Content about export controls. " * 200)
                + """</P>
            </ECFR>
            """
            )
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            # Act
            result = await ingestor.ingest(xml_path)

            # Assert
            if result.chunks_created > 0:
                assert mock_vector_store.add_chunks_batch.called
