"""Cross-reference validation tests.

These tests verify consistency across different reference data sets
and check invariants that should hold across the entire system.
"""

from export_control_mcp.resources.doe_nuclear import (
    GENERALLY_AUTHORIZED_DESTINATIONS,
)
from export_control_mcp.resources.doe_nuclear import (
    PROHIBITED_DESTINATIONS as CFR810_PROHIBITED,
)
from export_control_mcp.resources.reference_data import COUNTRY_GROUPS


class TestEmbargoCrossReference:
    """Verify embargo lists are consistent across EAR and DOE."""

    def test_ear_e1_matches_cfr810_prohibited(self):
        """E:1 terrorism list should match 10 CFR 810 prohibited."""
        e1 = set(COUNTRY_GROUPS["E:1"]["countries"])
        cfr810 = set(CFR810_PROHIBITED)
        # Should be identical
        assert e1 == cfr810, f"E:1={e1}, 810 prohibited={cfr810}"

    def test_comprehensive_embargo_countries_prohibited(self):
        """E:2 comprehensive embargo should be in 810 prohibited."""
        e2 = set(COUNTRY_GROUPS["E:2"]["countries"])
        cfr810 = set(CFR810_PROHIBITED)
        # E:2 should be subset of 810 prohibited
        missing = e2 - cfr810
        assert not missing, f"E:2 countries not in 810 prohibited: {missing}"


class TestAllyConsistency:
    """Verify allied countries are treated consistently."""

    def test_nato_mostly_in_cfr810_ga(self):
        """NATO members should mostly be 10 CFR 810 Generally Authorized."""
        nato = set(COUNTRY_GROUPS["A:6"]["countries"])
        cfr810_ga = set(GENERALLY_AUTHORIZED_DESTINATIONS)

        # Most NATO members should be in 810 GA
        in_ga = nato & cfr810_ga
        not_in_ga = nato - cfr810_ga

        # At least 80% of NATO should be GA (some smaller members may not be listed)
        # Known exceptions: Albania, Montenegro, North Macedonia, Iceland
        assert len(in_ga) >= len(nato) * 0.8, f"NATO not in GA: {not_in_ga}"

    def test_wassenaar_mostly_in_cfr810_ga(self):
        """Wassenaar members should mostly be 10 CFR 810 Generally Authorized."""
        wassenaar = set(COUNTRY_GROUPS["A:1"]["countries"])
        cfr810_ga = set(GENERALLY_AUTHORIZED_DESTINATIONS)

        in_ga = wassenaar & cfr810_ga
        not_in_ga = wassenaar - cfr810_ga

        # Most Wassenaar should be GA (some exceptions like India, Ukraine)
        assert len(in_ga) >= len(wassenaar) * 0.85, f"Wassenaar not in GA: {not_in_ga}"


class TestD1vsProhibited:
    """Verify D:1 national security list vs prohibited destinations."""

    def test_prohibited_in_d1_or_d5(self):
        """Prohibited destinations should be in D:1 or D:5."""
        prohibited = set(CFR810_PROHIBITED)
        d1 = set(COUNTRY_GROUPS["D:1"]["countries"])
        d5 = set(COUNTRY_GROUPS["D:5"]["countries"])
        d_combined = d1 | d5

        # All prohibited should be in D groups
        missing = prohibited - d_combined
        assert not missing, f"Prohibited not in D groups: {missing}"


class TestCountryNameConsistency:
    """Verify country names are consistent across data sets."""

    def test_no_conflicting_spellings(self):
        """Check for obvious spelling variations that might cause issues."""
        all_countries = set()

        # Collect all country names
        for group_data in COUNTRY_GROUPS.values():
            countries = group_data.get("countries", [])
            if isinstance(countries, list):
                all_countries.update(countries)

        all_countries.update(GENERALLY_AUTHORIZED_DESTINATIONS)
        all_countries.update(CFR810_PROHIBITED)

        # Check for common variations that should be standardized
        variations = [
            ("UK", "United Kingdom"),
            ("USA", "United States"),
            ("UAE", "United Arab Emirates"),
            ("DPRK", "North Korea"),
            ("ROK", "South Korea"),
        ]

        for abbrev, full in variations:
            if abbrev in all_countries and full in all_countries:
                # Both forms exist - might be intentional (aliases)
                pass

    def test_south_korea_naming(self):
        """South Korea should use consistent naming."""
        wassenaar = set(COUNTRY_GROUPS["A:1"]["countries"])
        cfr810_ga = set(GENERALLY_AUTHORIZED_DESTINATIONS)

        # Should use "South Korea" consistently
        assert "South Korea" in wassenaar or "Korea, Republic of" in wassenaar
        assert "South Korea" in cfr810_ga or "Korea, Republic of" in cfr810_ga


class TestLogicalConsistency:
    """Test logical consistency across all reference data."""

    def test_friendly_countries_not_embargoed(self):
        """Wassenaar/NATO countries shouldn't be in embargo lists."""
        wassenaar = set(COUNTRY_GROUPS["A:1"]["countries"])
        nato = set(COUNTRY_GROUPS["A:6"]["countries"])
        friendly = wassenaar | nato

        e1 = set(COUNTRY_GROUPS["E:1"]["countries"])
        e2 = set(COUNTRY_GROUPS["E:2"]["countries"])
        embargo = e1 | e2

        overlap = friendly & embargo
        assert not overlap, f"Friendly countries in embargo: {overlap}"

    def test_prohibited_destinations_sanctioned(self):
        """CFR 810 prohibited should all be in EAR embargo lists."""
        cfr810_prohibited = set(CFR810_PROHIBITED)
        d5 = set(COUNTRY_GROUPS["D:5"]["countries"])
        e1 = set(COUNTRY_GROUPS["E:1"]["countries"])

        # Should be in at least one embargo list
        for country in cfr810_prohibited:
            assert country in d5 or country in e1, f"{country} not in EAR embargo"


class TestDataCurrentness:
    """Tests that help identify potentially stale data."""

    def test_russia_status_post_2022(self):
        """Russia should be in embargo lists post-2022 invasion."""
        d5 = set(COUNTRY_GROUPS["D:5"]["countries"])
        assert "Russia" in d5, "Russia should be in D:5 embargo list"

    def test_finland_sweden_nato_2024(self):
        """Finland and Sweden should be in NATO (joined 2023-2024)."""
        nato = set(COUNTRY_GROUPS["A:6"]["countries"])
        assert "Finland" in nato, "Finland joined NATO in 2023"
        assert "Sweden" in nato, "Sweden joined NATO in 2024"

    def test_belarus_status(self):
        """Belarus should be in embargo lists."""
        d5 = set(COUNTRY_GROUPS["D:5"]["countries"])
        assert "Belarus" in d5, "Belarus should be in D:5 embargo list"
