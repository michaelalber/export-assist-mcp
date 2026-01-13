"""Tests for the sanctions list ingestion module."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from export_control_mcp.data.ingest.sanctions_ingest import (
    BIS_SOURCES,
    OFAC_SOURCES,
    SanctionsIngestor,
)
from export_control_mcp.models.sanctions import EntityType
from export_control_mcp.services.sanctions_db import SanctionsDBService


@pytest.fixture
def temp_db() -> SanctionsDBService:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_sanctions.db"
        db = SanctionsDBService(db_path=db_path)
        yield db
        db.close()


@pytest.fixture
def temp_download_dir() -> Path:
    """Create a temporary download directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sanctions_ingestor(temp_db: SanctionsDBService, temp_download_dir: Path) -> SanctionsIngestor:
    """Create sanctions ingestor with test dependencies."""
    return SanctionsIngestor(db=temp_db, download_dir=temp_download_dir)


class TestSourceURLs:
    """Tests for source URL constants."""

    def test_should_have_ofac_sdn_xml_url(self) -> None:
        """Test OFAC SDN XML URL is defined."""
        assert "sdn_xml" in OFAC_SOURCES
        assert "treasury.gov" in OFAC_SOURCES["sdn_xml"]

    def test_should_have_ofac_consolidated_xml_url(self) -> None:
        """Test OFAC consolidated XML URL is defined."""
        assert "consolidated_xml" in OFAC_SOURCES
        assert "treasury.gov" in OFAC_SOURCES["consolidated_xml"]

    def test_should_have_bis_denied_persons_url(self) -> None:
        """Test BIS Denied Persons List URL is defined."""
        assert "denied_persons_txt" in BIS_SOURCES
        assert "bis.doc.gov" in BIS_SOURCES["denied_persons_txt"]


class TestSDNTypMapping:
    """Tests for SDN type mapping."""

    def test_should_map_individual_type(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping 'Individual' to EntityType.INDIVIDUAL."""
        result = sanctions_ingestor._map_sdn_type("Individual")
        assert result == EntityType.INDIVIDUAL

    def test_should_map_entity_type(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping 'Entity' to EntityType.ENTITY."""
        result = sanctions_ingestor._map_sdn_type("Entity")
        assert result == EntityType.ENTITY

    def test_should_map_vessel_type(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping 'Vessel' to EntityType.VESSEL."""
        result = sanctions_ingestor._map_sdn_type("Vessel")
        assert result == EntityType.VESSEL

    def test_should_map_aircraft_type(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping 'Aircraft' to EntityType.AIRCRAFT."""
        result = sanctions_ingestor._map_sdn_type("Aircraft")
        assert result == EntityType.AIRCRAFT

    def test_should_default_to_entity_for_unknown(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test unknown types default to ENTITY."""
        result = sanctions_ingestor._map_sdn_type("Unknown")
        assert result == EntityType.ENTITY

    def test_should_handle_case_insensitive_matching(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test case-insensitive type matching."""
        assert sanctions_ingestor._map_sdn_type("INDIVIDUAL") == EntityType.INDIVIDUAL
        assert sanctions_ingestor._map_sdn_type("individual") == EntityType.INDIVIDUAL


class TestDateParsing:
    """Tests for date parsing utility."""

    def test_should_parse_iso_format(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test parsing ISO date format (YYYY-MM-DD)."""
        result = sanctions_ingestor._parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_should_parse_us_format(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test parsing US date format (MM/DD/YYYY)."""
        result = sanctions_ingestor._parse_date("01/15/2024")
        assert result == date(2024, 1, 15)

    def test_should_parse_dashed_us_format(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test parsing dashed US format (MM-DD-YYYY)."""
        result = sanctions_ingestor._parse_date("01-15-2024")
        assert result == date(2024, 1, 15)

    def test_should_parse_month_name_format(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test parsing format with month name (January 15, 2024)."""
        result = sanctions_ingestor._parse_date("January 15, 2024")
        assert result == date(2024, 1, 15)

    def test_should_parse_abbreviated_month_format(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test parsing format with abbreviated month (Jan 15, 2024)."""
        result = sanctions_ingestor._parse_date("Jan 15, 2024")
        assert result == date(2024, 1, 15)

    def test_should_return_none_for_empty_string(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test that empty string returns None."""
        result = sanctions_ingestor._parse_date("")
        assert result is None

    def test_should_return_none_for_invalid_date(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test that invalid date returns None."""
        result = sanctions_ingestor._parse_date("not a date")
        assert result is None


class TestCountryCodeNormalization:
    """Tests for country code normalization."""

    def test_should_return_2_letter_code_as_is(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test that 2-letter codes are returned unchanged."""
        assert sanctions_ingestor._normalize_country_code("CN") == "CN"
        assert sanctions_ingestor._normalize_country_code("RU") == "RU"

    def test_should_map_china_variants(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping China name variants."""
        assert sanctions_ingestor._normalize_country_code("China") == "CN"
        assert sanctions_ingestor._normalize_country_code("PEOPLE'S REPUBLIC OF CHINA") == "CN"
        assert sanctions_ingestor._normalize_country_code("PRC") == "CN"

    def test_should_map_russia_variants(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping Russia name variants."""
        assert sanctions_ingestor._normalize_country_code("Russia") == "RU"
        assert sanctions_ingestor._normalize_country_code("RUSSIAN FEDERATION") == "RU"

    def test_should_map_iran_variants(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping Iran name variants."""
        assert sanctions_ingestor._normalize_country_code("Iran") == "IR"
        assert sanctions_ingestor._normalize_country_code("ISLAMIC REPUBLIC OF IRAN") == "IR"

    def test_should_map_north_korea_variants(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping North Korea name variants."""
        assert sanctions_ingestor._normalize_country_code("North Korea") == "KP"
        assert sanctions_ingestor._normalize_country_code("DPRK") == "KP"

    def test_should_map_other_countries(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test mapping other common countries."""
        assert sanctions_ingestor._normalize_country_code("HONG KONG") == "HK"
        assert sanctions_ingestor._normalize_country_code("TAIWAN") == "TW"
        assert sanctions_ingestor._normalize_country_code("UAE") == "AE"

    def test_should_truncate_unknown_to_2_chars(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test that unknown country names are truncated to 2 chars."""
        result = sanctions_ingestor._normalize_country_code("Unknownland")
        assert len(result) == 2


class TestDeniedPersonsTXTParsing:
    """Tests for BIS Denied Persons List TXT parsing."""

    def test_should_parse_pipe_delimited_line(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test parsing pipe-delimited format."""
        # Arrange
        txt_content = """NAME|ADDRESS|EFFECTIVE DATE|EXPIRATION DATE|FR CITATION
John Doe|123 Test St, City, ST|2024-01-15|2034-01-15|99 FR 12345
Jane Smith|456 Sample Ave|2023-06-01||98 FR 54321"""
        txt_path = temp_download_dir / "dpl.txt"
        txt_path.write_text(txt_content)

        # Act
        entries = sanctions_ingestor._parse_bis_denied_persons_txt(txt_path)

        # Assert
        assert len(entries) == 2
        assert entries[0].name == "John Doe"
        assert "123 Test St" in entries[0].addresses[0]

    def test_should_skip_header_lines(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test that header lines are skipped."""
        # Arrange
        txt_content = """# BIS Denied Persons List
NAME|ADDRESS|EFFECTIVE DATE
Test Person|Test Address|2024-01-01"""
        txt_path = temp_download_dir / "dpl.txt"
        txt_path.write_text(txt_content)

        # Act
        entries = sanctions_ingestor._parse_bis_denied_persons_txt(txt_path)

        # Assert
        assert len(entries) == 1
        assert entries[0].name == "Test Person"

    def test_should_skip_empty_lines(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test that empty lines are skipped."""
        # Arrange
        txt_content = """John Doe|Address 1|2024-01-01

Jane Smith|Address 2|2024-02-02"""
        txt_path = temp_download_dir / "dpl.txt"
        txt_path.write_text(txt_content)

        # Act
        entries = sanctions_ingestor._parse_bis_denied_persons_txt(txt_path)

        # Assert
        assert len(entries) == 2

    def test_should_generate_sequential_ids(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test that IDs are generated sequentially."""
        # Arrange
        txt_content = """Person 1|Address|2024-01-01
Person 2|Address|2024-01-02
Person 3|Address|2024-01-03"""
        txt_path = temp_download_dir / "dpl.txt"
        txt_path.write_text(txt_content)

        # Act
        entries = sanctions_ingestor._parse_bis_denied_persons_txt(txt_path)

        # Assert
        assert all(e.id.startswith("DP-") for e in entries)
        ids = [e.id for e in entries]
        assert len(set(ids)) == 3  # All unique


class TestSDNXMLParsing:
    """Tests for OFAC SDN XML parsing."""

    def test_should_parse_sdn_xml_without_namespace(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test parsing SDN XML without namespace."""
        # Arrange
        xml_content = """<?xml version="1.0"?>
        <sdnList>
            <sdnEntry>
                <uid>12345</uid>
                <lastName>Test Entity Ltd</lastName>
                <sdnType>Entity</sdnType>
                <programList>
                    <program>IRAN</program>
                    <program>SDGT</program>
                </programList>
                <akaList>
                    <aka><lastName>TE Ltd</lastName></aka>
                </akaList>
                <remarks>Test remarks</remarks>
            </sdnEntry>
        </sdnList>
        """
        xml_path = temp_download_dir / "sdn.xml"
        xml_path.write_text(xml_content)

        # Act
        entries = sanctions_ingestor._parse_ofac_sdn_xml(xml_path)

        # Assert
        assert len(entries) == 1
        assert entries[0].name == "Test Entity Ltd"
        assert entries[0].sdn_type == EntityType.ENTITY
        assert "IRAN" in entries[0].programs
        assert "SDGT" in entries[0].programs
        assert "TE Ltd" in entries[0].aliases
        assert entries[0].remarks == "Test remarks"

    def test_should_combine_first_and_last_name_for_individuals(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test name combination for individuals."""
        # Arrange
        xml_content = """<?xml version="1.0"?>
        <sdnList>
            <sdnEntry>
                <uid>67890</uid>
                <firstName>John</firstName>
                <lastName>DOE</lastName>
                <sdnType>Individual</sdnType>
                <programList><program>SDGT</program></programList>
            </sdnEntry>
        </sdnList>
        """
        xml_path = temp_download_dir / "sdn.xml"
        xml_path.write_text(xml_content)

        # Act
        entries = sanctions_ingestor._parse_ofac_sdn_xml(xml_path)

        # Assert
        assert len(entries) == 1
        assert entries[0].name == "DOE, John"
        assert entries[0].sdn_type == EntityType.INDIVIDUAL

    def test_should_skip_entries_without_uid(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test that entries without UID are skipped."""
        # Arrange
        xml_content = """<?xml version="1.0"?>
        <sdnList>
            <sdnEntry>
                <lastName>No UID Entity</lastName>
                <sdnType>Entity</sdnType>
            </sdnEntry>
            <sdnEntry>
                <uid>12345</uid>
                <lastName>Has UID Entity</lastName>
                <sdnType>Entity</sdnType>
            </sdnEntry>
        </sdnList>
        """
        xml_path = temp_download_dir / "sdn.xml"
        xml_path.write_text(xml_content)

        # Act
        entries = sanctions_ingestor._parse_ofac_sdn_xml(xml_path)

        # Assert
        assert len(entries) == 1
        assert entries[0].name == "Has UID Entity"

    def test_should_parse_addresses(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test parsing address information."""
        # Arrange
        xml_content = """<?xml version="1.0"?>
        <sdnList>
            <sdnEntry>
                <uid>11111</uid>
                <lastName>Test Corp</lastName>
                <sdnType>Entity</sdnType>
                <addressList>
                    <address>
                        <address1>123 Main St</address1>
                        <city>Tehran</city>
                        <country>Iran</country>
                    </address>
                </addressList>
            </sdnEntry>
        </sdnList>
        """
        xml_path = temp_download_dir / "sdn.xml"
        xml_path.write_text(xml_content)

        # Act
        entries = sanctions_ingestor._parse_ofac_sdn_xml(xml_path)

        # Assert
        assert len(entries) == 1
        assert len(entries[0].addresses) == 1
        assert "123 Main St" in entries[0].addresses[0]
        assert "Tehran" in entries[0].addresses[0]


class TestEntityListExcelParsing:
    """Tests for BIS Entity List Excel parsing."""

    @pytest.mark.asyncio
    async def test_should_require_excel_path(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test that Excel path is required."""
        # Act
        result = await sanctions_ingestor.ingest_bis_entity_list(excel_path=None)

        # Assert
        assert len(result["errors"]) > 0
        assert "required" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_should_return_error_for_missing_file(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test error for non-existent file."""
        # Act
        result = await sanctions_ingestor.ingest_bis_entity_list(
            excel_path=Path("/nonexistent/file.xlsx")
        )

        # Assert
        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0].lower()


class TestFullIngestion:
    """Tests for full ingestion flow."""

    @pytest.mark.asyncio
    async def test_should_return_result_structure_for_sdn_ingestion(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test SDN ingestion returns proper result structure."""
        # Arrange - create test SDN file
        xml_content = """<?xml version="1.0"?>
        <sdnList>
            <sdnEntry>
                <uid>99999</uid>
                <lastName>Test Entity</lastName>
                <sdnType>Entity</sdnType>
                <programList><program>TEST</program></programList>
            </sdnEntry>
        </sdnList>
        """
        xml_path = temp_download_dir / "sdn.xml"
        xml_path.write_text(xml_content)

        # Act
        result = await sanctions_ingestor.ingest_ofac_sdn(force_download=False)

        # Assert
        assert "source" in result
        assert "entries_added" in result
        assert "errors" in result
        assert result["entries_added"] >= 1

    @pytest.mark.asyncio
    async def test_should_return_result_structure_for_denied_persons(
        self, sanctions_ingestor: SanctionsIngestor, temp_download_dir: Path
    ) -> None:
        """Test Denied Persons ingestion returns proper result structure."""
        # Arrange
        txt_content = "Test Person|123 Test St|2024-01-01||99 FR 12345"
        txt_path = temp_download_dir / "dpl.txt"
        txt_path.write_text(txt_content)

        # Act
        result = await sanctions_ingestor.ingest_bis_denied_persons(force_download=False)

        # Assert
        assert "source" in result
        assert "entries_added" in result
        assert result["entries_added"] >= 1


class TestGetText:
    """Tests for XML text extraction helper."""

    def test_should_return_text_from_child_element(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test extracting text from child element."""
        from xml.etree.ElementTree import Element

        # Arrange
        parent = Element("parent")
        child = Element("child")
        child.text = "  test value  "
        parent.append(child)

        # Act
        result = sanctions_ingestor._get_text(parent, "child")

        # Assert
        assert result == "test value"

    def test_should_return_none_for_missing_element(
        self, sanctions_ingestor: SanctionsIngestor
    ) -> None:
        """Test None is returned for missing child element."""
        from xml.etree.ElementTree import Element

        # Arrange
        parent = Element("parent")

        # Act
        result = sanctions_ingestor._get_text(parent, "nonexistent")

        # Assert
        assert result is None

    def test_should_return_none_for_empty_text(self, sanctions_ingestor: SanctionsIngestor) -> None:
        """Test None is returned for empty text content."""
        from xml.etree.ElementTree import Element

        # Arrange
        parent = Element("parent")
        child = Element("child")
        child.text = None
        parent.append(child)

        # Act
        result = sanctions_ingestor._get_text(parent, "child")

        # Assert
        assert result is None
