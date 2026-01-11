"""Data validation tests for 10 CFR 810 DOE nuclear reference data.

These tests verify that 10 CFR 810 data matches official DOE sources
for nuclear technology export controls.
"""

from export_control_mcp.resources.doe_nuclear import (
    GENERALLY_AUTHORIZED_ACTIVITIES,
    GENERALLY_AUTHORIZED_DESTINATIONS,
    PROHIBITED_DESTINATIONS,
    SPECIFIC_AUTHORIZATION_ACTIVITIES,
    SPECIFIC_AUTHORIZATION_WITH_123,
)


class TestProhibitedDestinations:
    """Verify 10 CFR 810.4 prohibited destinations."""

    def test_prohibited_count(self):
        """Should have exactly 4 prohibited destinations per 810.4."""
        assert len(PROHIBITED_DESTINATIONS) == 4

    def test_prohibited_countries(self):
        """Prohibited destinations per 10 CFR 810.4."""
        expected = {"Cuba", "Iran", "North Korea", "Syria"}
        actual = set(PROHIBITED_DESTINATIONS)
        assert actual == expected, f"Mismatch: got {actual}, expected {expected}"


class TestGenerallyAuthorizedDestinations:
    """Verify 10 CFR 810.6 Generally Authorized destinations."""

    def test_ga_minimum_count(self):
        """Should have ~47 Generally Authorized destinations."""
        # Allow some flexibility for list updates
        assert len(GENERALLY_AUTHORIZED_DESTINATIONS) >= 40

    def test_key_allies_present(self):
        """Key U.S. allies should be Generally Authorized."""
        # Note: Uses official names from 10 CFR 810 Appendix A
        key_allies = [
            "Australia",
            "Canada",
            "France",
            "Germany",
            "Japan",
            "Korea, Republic of",  # Official name per 10 CFR 810
            "United Kingdom",
        ]
        for country in key_allies:
            assert country in GENERALLY_AUTHORIZED_DESTINATIONS, f"Missing GA: {country}"

    def test_euratom_members_present(self):
        """EU/EURATOM members should be Generally Authorized."""
        euratom_members = [
            "Austria",
            "Belgium",
            "Finland",
            "France",
            "Germany",
            "Ireland",
            "Italy",
            "Netherlands",
            "Spain",
            "Sweden",
        ]
        for country in euratom_members:
            assert country in GENERALLY_AUTHORIZED_DESTINATIONS, f"Missing EURATOM: {country}"

    def test_iaea_safeguards_countries(self):
        """Countries with strong IAEA safeguards should be GA."""
        # Note: Not all IAEA safeguards countries are in 810 GA list
        safeguards_countries = [
            "Argentina",
            "Brazil",
            "Switzerland",
            "Norway",
        ]
        for country in safeguards_countries:
            assert country in GENERALLY_AUTHORIZED_DESTINATIONS, f"Missing: {country}"


class TestSpecificAuthorizationCountries:
    """Verify countries requiring specific authorization."""

    def test_123_agreement_countries_have_notes(self):
        """Countries with 123 agreements should have explanatory notes."""
        for country, info in SPECIFIC_AUTHORIZATION_WITH_123.items():
            assert "has_123_agreement" in info, f"{country} missing 123 flag"
            assert "notes" in info, f"{country} missing notes"

    def test_china_requires_specific(self):
        """China should require specific authorization."""
        assert "China" in SPECIFIC_AUTHORIZATION_WITH_123
        assert SPECIFIC_AUTHORIZATION_WITH_123["China"]["has_123_agreement"] is True

    def test_india_requires_specific(self):
        """India should require specific authorization."""
        assert "India" in SPECIFIC_AUTHORIZATION_WITH_123
        assert SPECIFIC_AUTHORIZATION_WITH_123["India"]["has_123_agreement"] is True

    def test_russia_requires_specific(self):
        """Russia should require specific authorization (123 suspended)."""
        assert "Russia" in SPECIFIC_AUTHORIZATION_WITH_123
        info = SPECIFIC_AUTHORIZATION_WITH_123["Russia"]
        assert info["has_123_agreement"] is True
        # Notes should mention suspension
        assert "suspend" in info["notes"].lower() or "suspen" in info["notes"].lower()


class TestGenerallyAuthorizedActivities:
    """Verify 10 CFR 810.6 Generally Authorized activities."""

    def test_activities_structure(self):
        """Each activity should have title and description."""
        for code, activity in GENERALLY_AUTHORIZED_ACTIVITIES.items():
            assert "title" in activity, f"{code} missing title"
            assert "description" in activity, f"{code} missing description"

    def test_section_numbers_valid(self):
        """Activity codes should reference 810.6 subsections."""
        for code in GENERALLY_AUTHORIZED_ACTIVITIES:
            assert code.startswith("810.6"), f"Invalid activity code: {code}"


class TestSpecificAuthorizationActivities:
    """Verify activities always requiring specific authorization."""

    def test_sensitive_activities_exist(self):
        """Sensitive nuclear activities should be defined."""
        sensitive = ["enrichment_technology", "reprocessing_technology", "heavy_water_production"]
        for activity in sensitive:
            assert activity in SPECIFIC_AUTHORIZATION_ACTIVITIES, f"Missing: {activity}"

    def test_sensitive_activities_require_specific(self):
        """Sensitive activities should always require specific authorization."""
        sensitive = ["enrichment_technology", "reprocessing_technology", "heavy_water_production"]
        for activity in sensitive:
            data = SPECIFIC_AUTHORIZATION_ACTIVITIES[activity]
            assert data["always_requires_specific"] is True, f"{activity} should require specific"

    def test_activities_have_descriptions(self):
        """All activities should have title and description."""
        for key, data in SPECIFIC_AUTHORIZATION_ACTIVITIES.items():
            assert "title" in data, f"{key} missing title"
            assert "description" in data, f"{key} missing description"


class TestCFR810Invariants:
    """Test logical invariants for 10 CFR 810 data."""

    def test_prohibited_not_generally_authorized(self):
        """No country can be both prohibited and Generally Authorized."""
        prohibited = set(PROHIBITED_DESTINATIONS)
        ga = set(GENERALLY_AUTHORIZED_DESTINATIONS)
        overlap = prohibited & ga
        assert not overlap, f"Countries in both prohibited and GA: {overlap}"

    def test_prohibited_not_specific_with_123(self):
        """Prohibited countries shouldn't have 123 agreements listed."""
        prohibited = set(PROHIBITED_DESTINATIONS)
        specific_123 = set(SPECIFIC_AUTHORIZATION_WITH_123.keys())
        overlap = prohibited & specific_123
        # Iran had a 123 agreement historically, so may be in both for documentation
        allowed = {"Iran"}
        unexpected = overlap - allowed
        assert not unexpected, f"Prohibited with 123: {unexpected}"

    def test_ga_and_specific_mutually_exclusive(self):
        """GA destinations shouldn't also require specific authorization."""
        ga = set(GENERALLY_AUTHORIZED_DESTINATIONS)
        specific = set(SPECIFIC_AUTHORIZATION_WITH_123.keys())
        overlap = ga & specific
        assert not overlap, f"Countries in both GA and specific: {overlap}"


class TestNPTConsistency:
    """Verify consistency with NPT (Non-Proliferation Treaty) status."""

    def test_nuclear_weapons_states_status(self):
        """NPT nuclear weapons states should have appropriate status."""
        # P5: US, Russia, UK, France, China
        # US is origin, not listed
        # UK, France should be GA (strong non-prolif)
        # Russia, China require specific auth
        assert "United Kingdom" in GENERALLY_AUTHORIZED_DESTINATIONS
        assert "France" in GENERALLY_AUTHORIZED_DESTINATIONS
        assert "Russia" in SPECIFIC_AUTHORIZATION_WITH_123
        assert "China" in SPECIFIC_AUTHORIZATION_WITH_123

    def test_non_npt_states_require_specific(self):
        """Non-NPT states should require specific authorization or be prohibited."""
        non_npt = ["India", "Pakistan", "Israel"]
        ga = set(GENERALLY_AUTHORIZED_DESTINATIONS)
        for country in non_npt:
            assert country not in ga, f"Non-NPT state {country} shouldn't be GA"
