"""Tests for the sanctions database service."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from export_control_mcp.models.sanctions import (
    CountrySanctions,
    DeniedPersonEntry,
    EntityListEntry,
    EntityType,
    SDNEntry,
)
from export_control_mcp.services.sanctions_db import SanctionsDBService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_sanctions.db"
        db = SanctionsDBService(db_path=db_path)
        yield db
        db.close()


@pytest.fixture
def sample_entity(temp_db):
    """Create a sample Entity List entry."""
    entry = EntityListEntry(
        id="TEST-001",
        name="Test Corporation Ltd.",
        aliases=["TestCorp", "TC Ltd"],
        addresses=["123 Test Street, Test City"],
        country="CN",
        license_requirement="For all items subject to the EAR",
        license_policy="Presumption of denial",
        federal_register_citation="99 FR 12345",
        effective_date=date(2023, 1, 15),
    )
    temp_db.add_entity_list_entry(entry)
    return entry


@pytest.fixture
def sample_sdn(temp_db):
    """Create a sample SDN entry."""
    entry = SDNEntry(
        id="SDN-TEST-001",
        name="Test Bank International",
        sdn_type=EntityType.ENTITY,
        programs=["IRAN", "SDGT"],
        aliases=["TBI", "Test Bank"],
        addresses=["Test Address, Iran"],
        remarks="Test entry for unit tests",
    )
    temp_db.add_sdn_entry(entry)
    return entry


@pytest.fixture
def sample_denied_person(temp_db):
    """Create a sample Denied Person entry."""
    entry = DeniedPersonEntry(
        id="DP-TEST-001",
        name="John Doe Test",
        addresses=["456 Sample Ave, Test City"],
        effective_date=date(2022, 6, 1),
        expiration_date=date(2032, 6, 1),
        federal_register_citation="99 FR 54321",
    )
    temp_db.add_denied_person(entry)
    return entry


class TestEntityListOperations:
    """Tests for Entity List database operations."""

    def test_add_and_search_entity(self, temp_db, sample_entity):
        """Test adding and searching for an entity."""
        results = temp_db.search_entity_list("Test Corporation")

        assert len(results) > 0
        assert results[0].entry.name == sample_entity.name

    def test_search_by_alias(self, temp_db, sample_entity):
        """Test searching by alias."""
        results = temp_db.search_entity_list("TestCorp", fuzzy_threshold=0.6)

        assert len(results) > 0
        assert sample_entity.id == results[0].entry.id

    def test_search_with_country_filter(self, temp_db, sample_entity):
        """Test filtering by country."""
        results = temp_db.search_entity_list("Test", country="CN")
        assert len(results) > 0

        results = temp_db.search_entity_list("Test", country="RU")
        assert len(results) == 0

    def test_fuzzy_search(self, temp_db, sample_entity):
        """Test fuzzy name matching."""
        # Slight misspelling
        results = temp_db.search_entity_list("Test Corpration", fuzzy_threshold=0.7)

        assert len(results) > 0


class TestSDNListOperations:
    """Tests for SDN List database operations."""

    def test_add_and_search_sdn(self, temp_db, sample_sdn):
        """Test adding and searching SDN entries."""
        results = temp_db.search_sdn_list("Test Bank")

        assert len(results) > 0
        assert results[0].entry.name == sample_sdn.name

    def test_search_by_type(self, temp_db, sample_sdn):
        """Test filtering by entity type."""
        results = temp_db.search_sdn_list("Test", sdn_type=EntityType.ENTITY)
        assert len(results) > 0

        results = temp_db.search_sdn_list("Test", sdn_type=EntityType.INDIVIDUAL)
        assert len(results) == 0

    def test_search_by_program(self, temp_db, sample_sdn):
        """Test filtering by sanctions program."""
        results = temp_db.search_sdn_list("Test", program="IRAN")
        assert len(results) > 0

        results = temp_db.search_sdn_list("Test", program="CUBA")
        assert len(results) == 0


class TestDeniedPersonsOperations:
    """Tests for Denied Persons List database operations."""

    def test_add_and_search_denied_person(self, temp_db, sample_denied_person):
        """Test adding and searching denied persons."""
        results = temp_db.search_denied_persons("John Doe")

        assert len(results) > 0
        assert results[0].entry.name == sample_denied_person.name

    def test_fuzzy_search_denied_person(self, temp_db, sample_denied_person):
        """Test fuzzy matching for denied persons."""
        results = temp_db.search_denied_persons("Jon Doe", fuzzy_threshold=0.7)

        assert len(results) > 0


class TestCountrySanctions:
    """Tests for country sanctions operations."""

    def test_add_and_get_country_sanctions(self, temp_db):
        """Test adding and retrieving country sanctions."""
        sanctions = CountrySanctions(
            country_code="XX",
            country_name="Test Country",
            ofac_programs=["TEST"],
            embargo_type="comprehensive",
            ear_country_groups=["E:1"],
            itar_restricted=True,
            arms_embargo=True,
            summary="Test sanctions profile",
            key_restrictions=["All exports prohibited"],
            notes=["Test note"],
        )
        temp_db.add_country_sanctions(sanctions)

        result = temp_db.get_country_sanctions("XX")

        assert result is not None
        assert result.country_name == "Test Country"
        assert result.embargo_type == "comprehensive"
        assert result.itar_restricted is True

    def test_get_country_by_name(self, temp_db):
        """Test looking up country by name."""
        sanctions = CountrySanctions(
            country_code="YY",
            country_name="Another Test Nation",
            ofac_programs=[],
            embargo_type="none",
            ear_country_groups=["B"],
            itar_restricted=False,
            arms_embargo=False,
            summary="Friendly test country",
        )
        temp_db.add_country_sanctions(sanctions)

        result = temp_db.get_country_by_name("Another Test")

        assert result is not None
        assert result.country_code == "YY"

    def test_country_not_found(self, temp_db):
        """Test handling of unknown country."""
        result = temp_db.get_country_sanctions("ZZ")
        assert result is None


class TestDatabaseUtilities:
    """Tests for database utility operations."""

    def test_get_stats(self, temp_db, sample_entity, sample_sdn, sample_denied_person):
        """Test database statistics."""
        stats = temp_db.get_stats()

        assert stats["entity_list"] >= 1
        assert stats["sdn_list"] >= 1
        assert stats["denied_persons"] >= 1

    def test_clear_all(self, temp_db, sample_entity, sample_sdn, sample_denied_person):
        """Test clearing all data."""
        temp_db.clear_all()
        stats = temp_db.get_stats()

        assert stats["entity_list"] == 0
        assert stats["sdn_list"] == 0
        assert stats["denied_persons"] == 0
