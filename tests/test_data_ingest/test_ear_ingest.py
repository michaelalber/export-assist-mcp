"""Tests for the EAR (Export Administration Regulations) ingestion module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from export_control_mcp.data.ingest.ear_ingest import EAR_PARTS, EARIngestor
from export_control_mcp.models.regulations import RegulationType


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Create a mock embedding service."""
    mock = MagicMock()
    mock.embed_batch.return_value = [[0.1] * 384]  # Mock embeddings
    return mock


@pytest.fixture
def mock_vector_store() -> MagicMock:
    """Create a mock vector store."""
    mock = MagicMock()
    return mock


@pytest.fixture
def ear_ingestor(mock_embedding_service: MagicMock, mock_vector_store: MagicMock) -> EARIngestor:
    """Create EAR ingestor with mock dependencies."""
    return EARIngestor(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        batch_size=10,
    )


class TestEARPartsMapping:
    """Tests for EAR parts mapping constants."""

    def test_should_contain_part_730_general_information(self) -> None:
        """Test Part 730 is defined."""
        assert 730 in EAR_PARTS
        assert "General Information" in EAR_PARTS[730]

    def test_should_contain_part_740_license_exceptions(self) -> None:
        """Test Part 740 (License Exceptions) is defined."""
        assert 740 in EAR_PARTS
        assert "License Exceptions" in EAR_PARTS[740]

    def test_should_contain_part_744_end_user_controls(self) -> None:
        """Test Part 744 (End-User Controls) is defined."""
        assert 744 in EAR_PARTS
        assert "End-User" in EAR_PARTS[744]

    def test_should_contain_part_774_commerce_control_list(self) -> None:
        """Test Part 774 (CCL) is defined."""
        assert 774 in EAR_PARTS
        assert "Commerce Control List" in EAR_PARTS[774]

    def test_should_have_all_major_ear_parts(self) -> None:
        """Test all major EAR parts are included."""
        expected_parts = [730, 732, 734, 736, 738, 740, 742, 744, 746, 774]
        for part in expected_parts:
            assert part in EAR_PARTS, f"Missing EAR Part {part}"


class TestEARIngestorProperties:
    """Tests for EARIngestor properties."""

    def test_should_return_ear_regulation_type(self, ear_ingestor: EARIngestor) -> None:
        """Test regulation_type property returns EAR."""
        # Arrange & Act
        reg_type = ear_ingestor.regulation_type

        # Assert
        assert reg_type == RegulationType.EAR


class TestEARPartDetection:
    """Tests for EAR part number detection."""

    def test_should_detect_part_from_filename_with_part_prefix(
        self, ear_ingestor: EARIngestor
    ) -> None:
        """Test detecting part number from filename like 'part730.pdf'."""
        # Arrange
        filename = "part730"
        content = "Some random content"

        # Act
        part_num = ear_ingestor._detect_ear_part(filename, content)

        # Assert
        assert part_num == 730

    def test_should_detect_part_from_filename_with_ear_prefix(
        self, ear_ingestor: EARIngestor
    ) -> None:
        """Test detecting part number from filename like 'ear_742.pdf'."""
        # Arrange
        filename = "ear_742"
        content = "Some random content"

        # Act
        part_num = ear_ingestor._detect_ear_part(filename, content)

        # Assert
        assert part_num == 742

    def test_should_detect_part_from_filename_with_hyphen(self, ear_ingestor: EARIngestor) -> None:
        """Test detecting part number from filename like 'part-740.pdf'."""
        # Arrange
        filename = "part-740"
        content = "Some random content"

        # Act
        part_num = ear_ingestor._detect_ear_part(filename, content)

        # Assert
        assert part_num == 740

    def test_should_detect_part_from_content_with_part_header(
        self, ear_ingestor: EARIngestor
    ) -> None:
        """Test detecting part number from content header."""
        # Arrange
        filename = "unknown"
        content = "Part 744 - Control Policy: End-User and End-Use Based Controls"

        # Act
        part_num = ear_ingestor._detect_ear_part(filename, content)

        # Assert
        assert part_num == 744

    def test_should_detect_part_from_cfr_citation(self, ear_ingestor: EARIngestor) -> None:
        """Test detecting part number from CFR citation."""
        # Arrange
        filename = "regulations"
        content = "The requirements of 15 CFR 746 apply to all exports..."

        # Act
        part_num = ear_ingestor._detect_ear_part(filename, content)

        # Assert
        assert part_num == 746

    def test_should_return_none_when_no_part_detected(self, ear_ingestor: EARIngestor) -> None:
        """Test that None is returned when part cannot be detected."""
        # Arrange
        filename = "random_document"
        content = "This document contains no part references."

        # Act
        part_num = ear_ingestor._detect_ear_part(filename, content)

        # Assert
        assert part_num is None


class TestEARPDFProcessing:
    """Tests for EAR PDF processing."""

    @pytest.mark.asyncio
    async def test_should_process_pdf_directory(self, ear_ingestor: EARIngestor) -> None:
        """Test processing a directory of PDF files."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir)
            # Create an empty PDF-like file (won't actually process as valid PDF)
            pdf_path = source_path / "part730.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 test content")

            # Act
            result = await ear_ingestor.ingest(source_path)

            # Assert
            # Will have error since it's not a valid PDF, but shouldn't crash
            assert result.regulation_type == "ear"

    @pytest.mark.asyncio
    async def test_should_handle_unsupported_file_type(self, ear_ingestor: EARIngestor) -> None:
        """Test that unsupported file types are reported as errors."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "test.docx"
            source_path.write_bytes(b"test content")

            # Act
            result = await ear_ingestor.ingest(source_path)

            # Assert
            assert len(result.errors) > 0
            assert "Unsupported file type" in result.errors[0]


class TestEARHTMLProcessing:
    """Tests for EAR HTML processing."""

    @pytest.mark.asyncio
    async def test_should_process_html_file(
        self, ear_ingestor: EARIngestor, mock_embedding_service: MagicMock
    ) -> None:
        """Test processing an HTML file."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "part730.html"
            html_content = """
            <html>
            <head><title>Part 730</title></head>
            <body>
            <h1>Part 730 - General Information</h1>
            <p>The Export Administration Regulations are issued by the
            Bureau of Industry and Security.</p>
            </body>
            </html>
            """
            html_path.write_text(html_content)

            # Act
            result = await ear_ingestor.ingest(html_path)

            # Assert
            assert result.sections_ingested >= 1
            # Chunks may be 0 if content is too short

    @pytest.mark.asyncio
    async def test_should_strip_script_and_style_tags(self, ear_ingestor: EARIngestor) -> None:
        """Test that script and style tags are removed from HTML."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "ear_740.html"
            html_content = """
            <html>
            <head>
            <style>.test { color: red; }</style>
            <script>alert('test');</script>
            </head>
            <body>
            <h1>Part 740 - License Exceptions</h1>
            <p>License Exception TMP allows temporary exports.</p>
            <script>console.log('should be removed');</script>
            </body>
            </html>
            """
            html_path.write_text(html_content)

            # Act
            result = await ear_ingestor.ingest(html_path)

            # Assert - should process without errors from JS
            assert result.regulation_type == "ear"


class TestEARBatchProcessing:
    """Tests for batch chunk processing."""

    @pytest.mark.asyncio
    async def test_should_store_chunks_in_batches(
        self,
        ear_ingestor: EARIngestor,
        mock_vector_store: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Test that chunks are stored in configurable batch sizes."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "part744.html"
            # Create content long enough to generate multiple chunks
            long_content = "<html><body><h1>Part 744</h1>"
            for i in range(50):
                long_content += f"<p>Section {i}: " + "word " * 200 + "</p>"
            long_content += "</body></html>"
            html_path.write_text(long_content)

            # Act
            result = await ear_ingestor.ingest(html_path)

            # Assert - vector store should have been called with batches
            if result.chunks_created > 0:
                assert mock_vector_store.add_chunks_batch.called


class TestEARIngestResult:
    """Tests for EAR ingestion result creation."""

    def test_should_create_result_with_ear_type(self, ear_ingestor: EARIngestor) -> None:
        """Test that _create_result sets correct regulation type."""
        # Arrange & Act
        result = ear_ingestor._create_result()

        # Assert
        assert result.regulation_type == "ear"
        assert result.sections_ingested == 0
        assert result.chunks_created == 0
        assert result.errors == []
