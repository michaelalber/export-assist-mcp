"""Tests for the base ingestor module."""

from export_control_mcp.data.ingest.base import IngestResult


class TestIngestResult:
    """Tests for IngestResult model."""

    def test_should_return_success_true_when_chunks_created_greater_than_zero(self) -> None:
        """Test that success is True when chunks are created."""
        # Arrange
        result = IngestResult(
            regulation_type="ear",
            sections_ingested=5,
            chunks_created=100,
            errors=[],
        )

        # Act
        success = result.success

        # Assert
        assert success is True

    def test_should_return_success_false_when_chunks_created_is_zero(self) -> None:
        """Test that success is False when no chunks are created."""
        # Arrange
        result = IngestResult(
            regulation_type="ear",
            sections_ingested=0,
            chunks_created=0,
            errors=["Some error"],
        )

        # Act
        success = result.success

        # Assert
        assert success is False

    def test_should_default_sections_ingested_to_zero(self) -> None:
        """Test default value for sections_ingested."""
        # Arrange & Act
        result = IngestResult(regulation_type="itar")

        # Assert
        assert result.sections_ingested == 0

    def test_should_default_chunks_created_to_zero(self) -> None:
        """Test default value for chunks_created."""
        # Arrange & Act
        result = IngestResult(regulation_type="itar")

        # Assert
        assert result.chunks_created == 0

    def test_should_default_errors_to_empty_list(self) -> None:
        """Test default value for errors."""
        # Arrange & Act
        result = IngestResult(regulation_type="ear")

        # Assert
        assert result.errors == []

    def test_should_allow_adding_errors_to_list(self) -> None:
        """Test that errors can be appended."""
        # Arrange
        result = IngestResult(regulation_type="ear")

        # Act
        result.errors.append("Error 1")
        result.errors.append("Error 2")

        # Assert
        assert len(result.errors) == 2
        assert "Error 1" in result.errors
        assert "Error 2" in result.errors

    def test_should_store_regulation_type(self) -> None:
        """Test that regulation type is stored correctly."""
        # Arrange & Act
        result = IngestResult(regulation_type="ear")

        # Assert
        assert result.regulation_type == "ear"
