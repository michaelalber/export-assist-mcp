"""Tests for sanctions search tools."""

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from export_control_mcp.models.sanctions import (
    DeniedPersonEntry,
    EntityListEntry,
    EntityType,
    SDNEntry,
)
from export_control_mcp.services.sanctions_db import SanctionsDBService


def create_test_db(tmpdir):
    """Create a test database with sample data."""
    db_path = Path(tmpdir) / "test_sanctions.db"
    db = SanctionsDBService(db_path=db_path)

    # Add sample Entity List entries
    db.add_entity_list_entry(
        EntityListEntry(
            id="EL-TEST-001",
            name="Sample Technology Corp",
            aliases=["STC", "SampleTech"],
            addresses=["Beijing, China"],
            country="CN",
            license_requirement="For all items subject to the EAR",
            license_policy="Presumption of denial",
            effective_date=date(2023, 1, 1),
        )
    )
    db.add_entity_list_entry(
        EntityListEntry(
            id="EL-TEST-002",
            name="Moscow Research Institute",
            aliases=["MRI"],
            addresses=["Moscow, Russia"],
            country="RU",
            license_requirement="For all items subject to the EAR",
            license_policy="Presumption of denial",
            effective_date=date(2022, 3, 1),
        )
    )

    # Add sample SDN entries
    db.add_sdn_entry(
        SDNEntry(
            id="SDN-TEST-001",
            name="Sanctioned Bank Ltd",
            sdn_type=EntityType.ENTITY,
            programs=["IRAN", "SDGT"],
            aliases=["SBL"],
            addresses=["Tehran, Iran"],
        )
    )
    db.add_sdn_entry(
        SDNEntry(
            id="SDN-TEST-002",
            name="Sanctioned Individual Person",
            sdn_type=EntityType.INDIVIDUAL,
            programs=["RUSSIA-EO14024"],
            aliases=["SIP"],
            nationalities=["Russia"],
        )
    )

    # Add sample Denied Person entries
    db.add_denied_person(
        DeniedPersonEntry(
            id="DP-TEST-001",
            name="Denied Exporter Inc",
            addresses=["Los Angeles, CA, USA"],
            effective_date=date(2021, 1, 1),
            expiration_date=date(2031, 1, 1),
        )
    )

    return db


@pytest.fixture
def sanctions_db():
    """Create a temporary sanctions database with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = create_test_db(tmpdir)
        yield db
        db.close()


@pytest.mark.asyncio
class TestSearchEntityList:
    """Tests for search_entity_list tool."""

    async def test_search_by_name(self, sanctions_db):
        """Test searching Entity List by name."""
        from export_control_mcp.tools.sanctions import search_entity_list

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_entity_list.fn
            results = await func("Sample Technology")

            assert len(results) > 0
            assert results[0]["entry"]["name"] == "Sample Technology Corp"

    async def test_search_by_alias(self, sanctions_db):
        """Test searching Entity List by alias."""
        from export_control_mcp.tools.sanctions import search_entity_list

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_entity_list.fn
            results = await func("STC")

            assert len(results) > 0
            assert "STC" in results[0]["entry"]["aliases"]

    async def test_search_with_country_filter(self, sanctions_db):
        """Test Entity List search with country filter."""
        from export_control_mcp.tools.sanctions import search_entity_list

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_entity_list.fn

            # Should find Chinese entity
            results = await func("Sample", country="CN")
            assert len(results) > 0

            # Should not find Russian entity
            results = await func("Sample", country="RU")
            assert len(results) == 0

    async def test_fuzzy_matching(self, sanctions_db):
        """Test fuzzy name matching."""
        from export_control_mcp.tools.sanctions import search_entity_list

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_entity_list.fn
            # Misspelled query
            results = await func("Sampl Technolgy", fuzzy_threshold=0.6)

            assert len(results) > 0


@pytest.mark.asyncio
class TestSearchSDNList:
    """Tests for search_sdn_list tool."""

    async def test_search_by_name(self, sanctions_db):
        """Test searching SDN List by name."""
        from export_control_mcp.tools.sanctions import search_sdn_list

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_sdn_list.fn
            results = await func("Sanctioned Bank")

            assert len(results) > 0
            assert results[0]["entry"]["name"] == "Sanctioned Bank Ltd"

    async def test_search_by_type(self, sanctions_db):
        """Test SDN search with entity type filter."""
        from export_control_mcp.tools.sanctions import search_sdn_list

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_sdn_list.fn

            # Search for entities
            results = await func("Sanctioned", entity_type="entity")
            assert len(results) > 0
            assert results[0]["entry"]["type"] == "entity"

            # Search for individuals
            results = await func("Sanctioned", entity_type="individual")
            assert len(results) > 0
            assert results[0]["entry"]["type"] == "individual"

    async def test_search_by_program(self, sanctions_db):
        """Test SDN search with program filter."""
        from export_control_mcp.tools.sanctions import search_sdn_list

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_sdn_list.fn

            # Search IRAN program
            results = await func("Sanctioned", program="IRAN")
            assert len(results) > 0

            # Search CUBA program (should find nothing)
            results = await func("Sanctioned", program="CUBA")
            assert len(results) == 0


@pytest.mark.asyncio
class TestSearchDeniedPersons:
    """Tests for search_denied_persons tool."""

    async def test_search_by_name(self, sanctions_db):
        """Test searching Denied Persons by name."""
        from export_control_mcp.tools.sanctions import search_denied_persons

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = search_denied_persons.fn
            results = await func("Denied Exporter")

            assert len(results) > 0
            assert results[0]["entry"]["name"] == "Denied Exporter Inc"


@pytest.mark.asyncio
class TestCheckCountrySanctions:
    """Tests for check_country_sanctions tool."""

    async def test_check_iran_sanctions(self, sanctions_db):
        """Test checking sanctions for Iran (comprehensive embargo)."""
        from export_control_mcp.tools.sanctions import check_country_sanctions

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = check_country_sanctions.fn
            result = await func("IR")

            assert "error" not in result
            assert result["country_code"] == "IR"
            assert result["embargo_type"] == "comprehensive"
            assert result["itar_restricted"] is True
            assert "IRAN" in result["ofac_programs"]

    async def test_check_russia_sanctions(self, sanctions_db):
        """Test checking sanctions for Russia (targeted sanctions)."""
        from export_control_mcp.tools.sanctions import check_country_sanctions

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = check_country_sanctions.fn
            result = await func("Russia")

            assert "error" not in result
            assert result["country_code"] == "RU"
            assert result["embargo_type"] == "targeted"

    async def test_check_friendly_country(self, sanctions_db):
        """Test checking sanctions for a friendly country."""
        from export_control_mcp.tools.sanctions import check_country_sanctions

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = check_country_sanctions.fn
            result = await func("Germany")

            assert "error" not in result
            assert result["embargo_type"] == "none"
            assert "A:1" in result["ear_country_groups"]

    async def test_check_unknown_country(self, sanctions_db):
        """Test checking sanctions for unknown country."""
        from export_control_mcp.tools.sanctions import check_country_sanctions

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = check_country_sanctions.fn
            result = await func("Nonexistent Country")

            assert "error" in result

    async def test_check_by_country_code(self, sanctions_db):
        """Test checking sanctions using country code."""
        from export_control_mcp.tools.sanctions import check_country_sanctions

        with patch("export_control_mcp.tools.sanctions.get_sanctions_db", return_value=sanctions_db):
            func = check_country_sanctions.fn
            result = await func("KP")

            assert "error" not in result
            assert result["country_name"] == "North Korea"
            assert result["embargo_type"] == "comprehensive"
