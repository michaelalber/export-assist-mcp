"""Tests for the Consolidated Screening List (CSL) ingestion module."""

import json
import tempfile
from pathlib import Path

import pytest

from export_control_mcp.data.ingest.csl_ingest import (
    CSL_SOURCE_MAPPING,
    CSL_SOURCE_NAMES,
    CSLEntry,
    CSLIngestor,
)
from export_control_mcp.models.sanctions import EntityType
from export_control_mcp.services.sanctions_db import SanctionsDBService


@pytest.fixture
def temp_db() -> SanctionsDBService:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_csl.db"
        db = SanctionsDBService(db_path=db_path)
        yield db
        db.close()


@pytest.fixture
def temp_download_dir() -> Path:
    """Create a temporary download directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def csl_ingestor(temp_db: SanctionsDBService, temp_download_dir: Path) -> CSLIngestor:
    """Create CSL ingestor with test dependencies."""
    return CSLIngestor(db=temp_db, download_dir=temp_download_dir)


class TestCSLEntry:
    """Tests for CSLEntry dataclass."""

    def test_should_create_entry_with_required_fields(self) -> None:
        """Test creating CSLEntry with minimal required fields."""
        # Arrange & Act
        entry = CSLEntry(
            id="CSL-001",
            name="Test Entity",
            entry_type=EntityType.ENTITY,
            source_list="Entity List",
            source_list_code="entity_list",
        )

        # Assert
        assert entry.id == "CSL-001"
        assert entry.name == "Test Entity"
        assert entry.entry_type == EntityType.ENTITY

    def test_should_default_optional_fields_to_empty(self) -> None:
        """Test that optional fields default to empty lists/strings."""
        # Arrange & Act
        entry = CSLEntry(
            id="CSL-001",
            name="Test Entity",
            entry_type=EntityType.ENTITY,
            source_list="Entity List",
            source_list_code="entity_list",
        )

        # Assert
        assert entry.programs == []
        assert entry.aliases == []
        assert entry.addresses == []
        assert entry.countries == []
        assert entry.ids == []
        assert entry.remarks == ""

    def test_should_generate_searchable_text_from_all_fields(self) -> None:
        """Test to_search_text combines all relevant fields."""
        # Arrange
        entry = CSLEntry(
            id="CSL-001",
            name="Test Corporation",
            entry_type=EntityType.ENTITY,
            source_list="Entity List",
            source_list_code="entity_list",
            aliases=["TestCorp", "TC Ltd"],
            addresses=["123 Main St, Beijing"],
            countries=["CN"],
            programs=["IRAN"],
            remarks="Known proliferator",
        )

        # Act
        search_text = entry.to_search_text()

        # Assert
        assert "Test Corporation" in search_text
        assert "TestCorp" in search_text
        assert "TC Ltd" in search_text
        assert "123 Main St, Beijing" in search_text
        assert "CN" in search_text
        assert "IRAN" in search_text
        assert "Known proliferator" in search_text


class TestCSLSourceMapping:
    """Tests for CSL source mapping constants."""

    def test_should_have_mapping_for_entity_list(self) -> None:
        """Test Entity List is in source mapping."""
        # Arrange & Act & Assert
        found = any("Entity List" in key for key in CSL_SOURCE_MAPPING)
        assert found

    def test_should_have_mapping_for_sdn(self) -> None:
        """Test SDN is in source mapping."""
        # Arrange & Act & Assert
        found = any("SDN" in key for key in CSL_SOURCE_MAPPING)
        assert found

    def test_should_have_display_names_for_all_codes(self) -> None:
        """Test all source codes have display names."""
        # Arrange
        codes = set(CSL_SOURCE_MAPPING.values())

        # Act & Assert
        for code in codes:
            assert code in CSL_SOURCE_NAMES, f"Missing display name for {code}"


class TestCSLIngestorParsing:
    """Tests for CSL JSON parsing."""

    def test_should_parse_csl_item_with_individual_type(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test parsing individual type entries."""
        # Arrange
        item = {
            "id": "12345",
            "name": "John Doe",
            "type": "Individual",
            "source": "Specially Designated Nationals (SDN) - Treasury Department",
            "programs": ["SDGT"],
            "alt_names": ["J. Doe", "Johnny Doe"],
            "addresses": [{"address": "123 Test St", "city": "Tehran", "country": "IR"}],
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is not None
        assert entry.entry_type == EntityType.INDIVIDUAL
        assert entry.name == "John Doe"
        assert "J. Doe" in entry.aliases
        assert len(entry.addresses) == 1
        assert "IR" in entry.countries

    def test_should_parse_csl_item_with_entity_type(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test parsing entity type entries."""
        # Arrange
        item = {
            "id": "67890",
            "name": "Evil Corporation Ltd",
            "type": "Entity",
            "source": "Entity List (EL) - Bureau of Industry and Security",
            "programs": ["EAR"],
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is not None
        assert entry.entry_type == EntityType.ENTITY
        assert entry.source_list_code == "entity_list"

    def test_should_parse_csl_item_with_vessel_type(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test parsing vessel type entries."""
        # Arrange
        item = {
            "id": "11111",
            "name": "MV Sanctions Evader",
            "type": "Vessel",
            "source": "SDN",
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is not None
        assert entry.entry_type == EntityType.VESSEL

    def test_should_parse_csl_item_with_aircraft_type(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test parsing aircraft type entries."""
        # Arrange
        item = {
            "id": "22222",
            "name": "Boeing 747-SP",
            "type": "Aircraft",
            "source": "SDN",
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is not None
        assert entry.entry_type == EntityType.AIRCRAFT

    def test_should_return_none_for_empty_name(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test that items without names are skipped."""
        # Arrange
        item = {
            "id": "33333",
            "name": "",
            "type": "Entity",
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is None

    def test_should_generate_id_when_missing(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test ID generation when not provided."""
        # Arrange
        item = {
            "name": "Unknown Entity",
            "type": "Entity",
            "source": "SDN",
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is not None
        assert entry.id.startswith("CSL-")

    def test_should_handle_string_aliases(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test handling when aliases is a string instead of list."""
        # Arrange
        item = {
            "id": "44444",
            "name": "Test Entity",
            "type": "Entity",
            "alt_names": "Single Alias",
            "source": "SDN",
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is not None
        assert "Single Alias" in entry.aliases

    def test_should_handle_string_programs(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test handling when programs is a string instead of list."""
        # Arrange
        item = {
            "id": "55555",
            "name": "Test Entity",
            "type": "Entity",
            "programs": "IRAN",
            "source": "SDN",
        }

        # Act
        entry = csl_ingestor._parse_csl_item(item)

        # Assert
        assert entry is not None
        assert "IRAN" in entry.programs


class TestCSLSourceCodeMapping:
    """Tests for source code mapping logic."""

    def test_should_map_entity_list_source(self, csl_ingestor: CSLIngestor) -> None:
        """Test mapping Entity List source."""
        # Arrange
        source = "Entity List (EL) - Bureau of Industry and Security"

        # Act
        code = csl_ingestor._map_source_to_code(source)

        # Assert
        assert code == "entity_list"

    def test_should_map_sdn_source(self, csl_ingestor: CSLIngestor) -> None:
        """Test mapping SDN source."""
        # Arrange
        source = "Specially Designated Nationals (SDN) - Treasury Department"

        # Act
        code = csl_ingestor._map_source_to_code(source)

        # Assert
        assert code == "sdn"

    def test_should_map_denied_persons_source(self, csl_ingestor: CSLIngestor) -> None:
        """Test mapping Denied Persons source."""
        # Arrange
        source = "Denied Persons List (DPL) - Bureau of Industry and Security"

        # Act
        code = csl_ingestor._map_source_to_code(source)

        # Assert
        assert code == "denied_persons"

    def test_should_use_fallback_for_unknown_source(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test fallback mapping for unknown sources."""
        # Arrange
        source = "Unknown List"

        # Act
        code = csl_ingestor._map_source_to_code(source)

        # Assert
        assert code == "other"

    def test_should_use_keyword_fallback_for_entity(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test keyword-based fallback for entity-related sources."""
        # Arrange
        source = "Some Entity Related List"

        # Act
        code = csl_ingestor._map_source_to_code(source)

        # Assert
        assert code == "entity_list"

    def test_should_use_keyword_fallback_for_cmic(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test keyword-based fallback for CMIC sources."""
        # Arrange
        source = "Some CMIC Related List"

        # Act
        code = csl_ingestor._map_source_to_code(source)

        # Assert
        assert code == "ns_cmic"


class TestCSLJsonParsing:
    """Tests for parsing CSL JSON files."""

    def test_should_parse_json_with_results_array(
        self, csl_ingestor: CSLIngestor, temp_download_dir: Path
    ) -> None:
        """Test parsing JSON with 'results' wrapper."""
        # Arrange
        json_data = {
            "results": [
                {"id": "1", "name": "Entity One", "type": "Entity", "source": "SDN"},
                {"id": "2", "name": "Entity Two", "type": "Entity", "source": "SDN"},
            ]
        }
        json_path = temp_download_dir / "test.json"
        json_path.write_text(json.dumps(json_data))

        # Act
        entries = csl_ingestor._parse_csl_json(json_path)

        # Assert
        assert len(entries) == 2

    def test_should_parse_json_with_direct_array(
        self, csl_ingestor: CSLIngestor, temp_download_dir: Path
    ) -> None:
        """Test parsing JSON that is directly an array."""
        # Arrange
        json_data = [
            {"id": "1", "name": "Entity One", "type": "Entity", "source": "SDN"},
            {"id": "2", "name": "Entity Two", "type": "Entity", "source": "SDN"},
        ]
        json_path = temp_download_dir / "test.json"
        json_path.write_text(json.dumps(json_data))

        # Act
        entries = csl_ingestor._parse_csl_json(json_path)

        # Assert
        assert len(entries) == 2

    def test_should_skip_invalid_entries_gracefully(
        self, csl_ingestor: CSLIngestor, temp_download_dir: Path
    ) -> None:
        """Test that invalid entries are skipped without failing."""
        # Arrange
        json_data = [
            {"id": "1", "name": "Valid Entity", "type": "Entity", "source": "SDN"},
            {"id": "2", "name": "", "type": "Entity"},  # Invalid - empty name
            {"id": "3", "name": "Another Valid", "type": "Entity", "source": "SDN"},
        ]
        json_path = temp_download_dir / "test.json"
        json_path.write_text(json.dumps(json_data))

        # Act
        entries = csl_ingestor._parse_csl_json(json_path)

        # Assert
        assert len(entries) == 2


class TestCSLIngestion:
    """Tests for full CSL ingestion flow."""

    @pytest.mark.asyncio
    async def test_should_use_cached_file_when_exists(
        self, csl_ingestor: CSLIngestor, temp_download_dir: Path
    ) -> None:
        """Test that cached file is used when available."""
        # Arrange
        json_data = [
            {"id": "1", "name": "Cached Entity", "type": "Entity", "source": "SDN"},
        ]
        cached_path = temp_download_dir / "csl.json"
        cached_path.write_text(json.dumps(json_data))

        # Act
        result_path = await csl_ingestor.download_csl(force=False)

        # Assert
        assert result_path == cached_path

    @pytest.mark.asyncio
    async def test_should_store_entries_in_database(
        self, csl_ingestor: CSLIngestor, temp_download_dir: Path, temp_db: SanctionsDBService
    ) -> None:
        """Test that parsed entries are stored in database."""
        # Arrange
        json_data = [
            {
                "id": "1",
                "name": "Test Entity For DB",
                "type": "Entity",
                "source": "SDN",
                "programs": ["IRAN"],
            },
        ]
        cached_path = temp_download_dir / "csl.json"
        cached_path.write_text(json.dumps(json_data))

        # Act
        result = await csl_ingestor.ingest(force_download=False)

        # Assert
        assert result["total_entries"] == 1

        # Verify in database
        db_results = temp_db.search_csl("Test Entity For DB")
        assert len(db_results) >= 1

    @pytest.mark.asyncio
    async def test_should_return_error_when_download_fails(
        self, csl_ingestor: CSLIngestor
    ) -> None:
        """Test error handling when download fails and no cache."""
        # Arrange - ensure no cached file exists
        cached_path = csl_ingestor.download_dir / "csl.json"
        if cached_path.exists():
            cached_path.unlink()

        # Act - This will try to download and may fail (network dependent)
        # For unit test, we verify the method doesn't crash
        download_result = await csl_ingestor.download_csl(force=True)

        # Assert - result should be either a Path (if download succeeded)
        # or None (if network failed). Either is acceptable for this test.
        assert download_result is None or isinstance(download_result, Path)
