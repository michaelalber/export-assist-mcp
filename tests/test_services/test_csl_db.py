"""Tests for Consolidated Screening List database operations."""

import pytest

from export_control_mcp.services.sanctions_db import SanctionsDBService


@pytest.fixture
def temp_csl_db(tmp_path):
    """Create a temporary database for CSL testing."""
    db_path = tmp_path / "test_csl.db"
    db = SanctionsDBService(str(db_path))
    yield db


@pytest.fixture
def sample_csl_entries(temp_csl_db):
    """Add sample CSL entries for testing."""
    entries = [
        {
            "entry_id": "CSL-001",
            "name": "Acme Defense Industries",
            "entry_type": "entity",
            "source_list": "entity_list",
            "programs": ["EAR"],
            "aliases": ["Acme Defense", "ADI Corp"],
            "addresses": ["123 Main St, Beijing, China"],
            "countries": ["China"],
            "remarks": "Added for missile technology concerns",
        },
        {
            "entry_id": "CSL-002",
            "name": "Ivan Petrov",
            "entry_type": "individual",
            "source_list": "sdn",
            "programs": ["RUSSIA-EO14024", "UKRAINE-EO13660"],
            "aliases": ["I. Petrov", "Petrov Ivan"],
            "addresses": ["Moscow, Russia"],
            "countries": ["Russia"],
            "remarks": "Designated for sanctions evasion",
        },
        {
            "entry_id": "CSL-003",
            "name": "Tehran Trading Company",
            "entry_type": "entity",
            "source_list": "sdn",
            "programs": ["IRAN", "NPWMD"],
            "aliases": ["TTC", "Tehran Traders"],
            "addresses": ["Tehran, Iran"],
            "countries": ["Iran"],
            "remarks": "Proliferation concern",
        },
        {
            "entry_id": "CSL-004",
            "name": "Global Shipping LLC",
            "entry_type": "entity",
            "source_list": "denied_persons",
            "programs": [],
            "aliases": [],
            "addresses": ["456 Port Ave, Shanghai, China"],
            "countries": ["China"],
            "remarks": "Export violations",
        },
    ]

    for entry in entries:
        temp_csl_db.add_csl_entry(**entry)

    return entries


class TestCSLDatabaseOperations:
    """Tests for CSL database CRUD operations."""

    def test_add_csl_entry(self, temp_csl_db):
        """Test adding a CSL entry."""
        temp_csl_db.add_csl_entry(
            entry_id="CSL-TEST",
            name="Test Entity",
            entry_type="entity",
            source_list="entity_list",
            programs=["EAR"],
            aliases=["Test"],
            addresses=["123 Test St"],
            countries=["US"],
            remarks="Test entry",
        )
        results = temp_csl_db.search_csl("Test Entity")
        assert len(results) == 1
        assert results[0]["name"] == "Test Entity"

    def test_search_csl_by_name(self, temp_csl_db, sample_csl_entries):
        """Test searching CSL by exact name."""
        results = temp_csl_db.search_csl("Acme Defense Industries")
        assert len(results) >= 1
        assert any(r["name"] == "Acme Defense Industries" for r in results)

    def test_search_csl_by_alias(self, temp_csl_db, sample_csl_entries):
        """Test searching CSL by alias."""
        results = temp_csl_db.search_csl("ADI Corp")
        assert len(results) >= 1
        assert any("Acme" in r["name"] for r in results)

    def test_search_csl_partial_match(self, temp_csl_db, sample_csl_entries):
        """Test partial name matching."""
        results = temp_csl_db.search_csl("Tehran")
        assert len(results) >= 1
        assert any("Tehran" in r["name"] for r in results)

    def test_search_csl_by_source_list(self, temp_csl_db, sample_csl_entries):
        """Test filtering by source list with query."""
        # Search with a query that matches entries in that source
        results = temp_csl_db.search_csl("Petrov", source_list="sdn")
        assert len(results) >= 1
        for r in results:
            assert r["source_list"] == "sdn"

    def test_search_csl_no_results(self, temp_csl_db, sample_csl_entries):
        """Test search with no matching results."""
        results = temp_csl_db.search_csl("Nonexistent Company XYZ123")
        assert len(results) == 0

    def test_clear_csl(self, temp_csl_db, sample_csl_entries):
        """Test clearing all CSL entries."""
        # Verify entries exist by searching
        results = temp_csl_db.search_csl("Acme")
        assert len(results) > 0

        # Clear and verify empty
        temp_csl_db.clear_csl()

        # Stats should show no entries
        stats = temp_csl_db.get_csl_stats()
        total = sum(stats.values())
        assert total == 0

    def test_get_csl_stats(self, temp_csl_db, sample_csl_entries):
        """Test getting CSL statistics."""
        stats = temp_csl_db.get_csl_stats()
        # Stats returns {source_list: count, ...}
        assert "entity_list" in stats
        assert "sdn" in stats
        assert stats["sdn"] == 2  # Petrov and Tehran Trading
        assert stats["entity_list"] == 1  # Acme
        assert stats["denied_persons"] == 1  # Global Shipping


class TestCSLEdgeCases:
    """Tests for CSL edge cases and special scenarios."""

    def test_special_characters_in_name(self, temp_csl_db):
        """Test handling of special characters in names."""
        temp_csl_db.add_csl_entry(
            entry_id="CSL-SPECIAL",
            name="O'Brien Associates Ltd",
            entry_type="entity",
            source_list="entity_list",
            programs=[],
            aliases=[],
            addresses=[],
            countries=[],
            remarks="",
        )
        results = temp_csl_db.search_csl("O'Brien")
        assert len(results) >= 1

    def test_unicode_characters(self, temp_csl_db):
        """Test handling of unicode/international characters."""
        temp_csl_db.add_csl_entry(
            entry_id="CSL-UNICODE",
            name="Müller GmbH",
            entry_type="entity",
            source_list="entity_list",
            programs=[],
            aliases=["Mueller GmbH"],
            addresses=["Berlin, Deutschland"],
            countries=["Germany"],
            remarks="",
        )
        results = temp_csl_db.search_csl("Müller")
        assert len(results) >= 1

    def test_empty_optional_fields(self, temp_csl_db):
        """Test entry with minimal required fields."""
        temp_csl_db.add_csl_entry(
            entry_id="CSL-MINIMAL",
            name="Minimal Entry",
            entry_type="entity",
            source_list="other",
            programs=[],
            aliases=[],
            addresses=[],
            countries=[],
            remarks="",
        )
        results = temp_csl_db.search_csl("Minimal Entry")
        assert len(results) == 1

    def test_case_insensitive_search(self, temp_csl_db, sample_csl_entries):
        """Test that search is case-insensitive."""
        results_lower = temp_csl_db.search_csl("acme defense")
        results_upper = temp_csl_db.search_csl("ACME DEFENSE")
        results_mixed = temp_csl_db.search_csl("Acme Defense")

        # All should find results
        assert len(results_lower) >= 1
        assert len(results_upper) >= 1
        assert len(results_mixed) >= 1
