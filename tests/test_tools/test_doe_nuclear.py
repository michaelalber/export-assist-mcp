"""Tests for DOE Nuclear (10 CFR 810) resources and logic.

These tests focus on the business logic in the resource module.
MCP tool wrapper tests are in the integration test suite.
"""

import pytest

from export_control_mcp.resources.doe_nuclear import (
    CFR810AuthorizationType,
    GENERALLY_AUTHORIZED_ACTIVITIES,
    GENERALLY_AUTHORIZED_DESTINATIONS,
    PROHIBITED_DESTINATIONS,
    SPECIFIC_AUTHORIZATION_ACTIVITIES,
    SPECIFIC_AUTHORIZATION_WITH_123,
    get_all_generally_authorized,
    get_all_prohibited,
    get_cfr810_authorization,
    is_generally_authorized,
    is_prohibited_destination,
)


class TestGetCFR810Authorization:
    """Tests for the get_cfr810_authorization resource function."""

    def test_generally_authorized_country(self):
        """Test lookup of Generally Authorized destination."""
        result = get_cfr810_authorization("Japan")
        assert result is not None
        assert result.name == "Japan"
        assert result.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED
        assert result.iso_code == "JP"

    def test_prohibited_country(self):
        """Test lookup of prohibited destination."""
        result = get_cfr810_authorization("Iran")
        assert result is not None
        assert result.name == "Iran"
        assert result.authorization_type == CFR810AuthorizationType.PROHIBITED

    def test_specific_authorization_country(self):
        """Test lookup of country requiring specific authorization."""
        result = get_cfr810_authorization("China")
        assert result is not None
        assert result.name == "China"
        assert result.authorization_type == CFR810AuthorizationType.SPECIFIC_AUTHORIZATION
        assert result.has_123_agreement is True

    def test_case_insensitive_lookup(self):
        """Test that country lookup is case-insensitive."""
        result = get_cfr810_authorization("JAPAN")
        assert result is not None
        assert result.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED

    def test_country_name_variations(self):
        """Test common country name variations."""
        # South Korea variations
        result1 = get_cfr810_authorization("South Korea")
        result2 = get_cfr810_authorization("Korea, Republic of")
        assert result1 is not None
        assert result2 is not None
        assert result1.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED
        assert result2.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED

        # UK variations
        result3 = get_cfr810_authorization("UK")
        assert result3 is not None
        assert result3.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED

    def test_unknown_country_defaults_to_specific(self):
        """Test that unknown countries default to specific authorization."""
        result = get_cfr810_authorization("Wakanda")
        assert result is not None
        assert result.authorization_type == CFR810AuthorizationType.SPECIFIC_AUTHORIZATION
        assert result.has_123_agreement is False

    def test_helper_functions(self):
        """Test is_generally_authorized and is_prohibited_destination helpers."""
        assert is_generally_authorized("Germany") is True
        assert is_generally_authorized("Iran") is False
        assert is_generally_authorized("China") is False

        assert is_prohibited_destination("Iran") is True
        assert is_prohibited_destination("North Korea") is True
        assert is_prohibited_destination("Germany") is False

    def test_get_all_lists(self):
        """Test getting all countries in each category."""
        ga_list = get_all_generally_authorized()
        prohibited_list = get_all_prohibited()

        assert len(ga_list) >= 40  # Should have 40+ Generally Authorized
        assert "Japan" in ga_list
        assert "Germany" in ga_list

        assert len(prohibited_list) == 4  # Cuba, Iran, North Korea, Syria
        assert "Iran" in prohibited_list


class TestCFR810ReferenceData:
    """Tests for 10 CFR 810 reference data completeness and accuracy."""

    def test_generally_authorized_destinations_count(self):
        """Verify expected number of GA destinations."""
        assert len(GENERALLY_AUTHORIZED_DESTINATIONS) >= 40
        # Key allies should be present
        assert "Canada" in GENERALLY_AUTHORIZED_DESTINATIONS
        assert "United Kingdom" in GENERALLY_AUTHORIZED_DESTINATIONS
        assert "Australia" in GENERALLY_AUTHORIZED_DESTINATIONS
        assert "Japan" in GENERALLY_AUTHORIZED_DESTINATIONS

    def test_prohibited_destinations(self):
        """Verify prohibited destinations list."""
        expected = {"Cuba", "Iran", "North Korea", "Syria"}
        assert set(PROHIBITED_DESTINATIONS) == expected

    def test_specific_authorization_countries_have_notes(self):
        """Verify countries with 123 agreements have explanatory notes."""
        for country, info in SPECIFIC_AUTHORIZATION_WITH_123.items():
            assert "has_123_agreement" in info
            assert "notes" in info
            assert info["notes"], f"{country} should have notes"

    def test_generally_authorized_activities_structure(self):
        """Verify activity data structure."""
        for code, activity in GENERALLY_AUTHORIZED_ACTIVITIES.items():
            assert "title" in activity
            assert "description" in activity
            assert code.startswith("810.6")

    def test_specific_authorization_activities_structure(self):
        """Verify specific authorization activity data."""
        for key, activity in SPECIFIC_AUTHORIZATION_ACTIVITIES.items():
            assert "title" in activity
            assert "description" in activity
            assert "always_requires_specific" in activity

    def test_sensitive_technologies_require_specific_auth(self):
        """Verify sensitive nuclear technologies require specific authorization."""
        sensitive_activities = SPECIFIC_AUTHORIZATION_ACTIVITIES
        assert "enrichment_technology" in sensitive_activities
        assert "reprocessing_technology" in sensitive_activities
        assert "heavy_water_production" in sensitive_activities

        for key in ["enrichment_technology", "reprocessing_technology", "heavy_water_production"]:
            assert sensitive_activities[key]["always_requires_specific"] is True


class TestCFR810EdgeCases:
    """Edge case tests for 10 CFR 810 lookups."""

    def test_whitespace_handling(self):
        """Test that whitespace in country names is handled."""
        result = get_cfr810_authorization("  Japan  ")
        assert result is not None
        assert result.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED

    def test_dprk_alias(self):
        """Test DPRK alias for North Korea."""
        result = get_cfr810_authorization("DPRK")
        assert result is not None
        assert result.authorization_type == CFR810AuthorizationType.PROHIBITED

    def test_uae_alias(self):
        """Test UAE alias for United Arab Emirates."""
        result = get_cfr810_authorization("UAE")
        assert result is not None
        assert result.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED

    def test_russia_requires_specific(self):
        """Russia should require specific authorization (123 suspended)."""
        result = get_cfr810_authorization("Russia")
        assert result is not None
        assert result.authorization_type == CFR810AuthorizationType.SPECIFIC_AUTHORIZATION
        assert result.has_123_agreement is True  # Has agreement but suspended

    def test_india_requires_specific(self):
        """India has 123 agreement but requires specific authorization."""
        result = get_cfr810_authorization("India")
        assert result is not None
        assert result.authorization_type == CFR810AuthorizationType.SPECIFIC_AUTHORIZATION
        assert result.has_123_agreement is True
