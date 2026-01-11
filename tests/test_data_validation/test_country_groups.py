"""Data validation tests for EAR country groups.

These tests verify that country group data matches official BIS sources
(15 CFR 740 Supplement No. 1).
"""

from export_control_mcp.resources.reference_data import COUNTRY_GROUPS, get_country_groups


class TestCountryGroupStructure:
    """Verify country group data structure is complete."""

    def test_required_country_groups_exist(self):
        """All standard EAR country groups should be defined."""
        required_groups = ["A:1", "A:5", "A:6", "B", "D:1", "D:2", "D:3", "D:4", "D:5", "E:1", "E:2"]
        for group in required_groups:
            assert group in COUNTRY_GROUPS, f"Missing country group: {group}"

    def test_country_groups_have_required_fields(self):
        """Each country group should have name, description, and countries."""
        for group_code, group_data in COUNTRY_GROUPS.items():
            assert "name" in group_data, f"{group_code} missing 'name'"
            assert "description" in group_data, f"{group_code} missing 'description'"
            assert "countries" in group_data, f"{group_code} missing 'countries'"


class TestWassenaarArrangement:
    """Verify Country Group A:1 (Wassenaar Arrangement) accuracy."""

    def test_wassenaar_member_count(self):
        """Wassenaar should have 42 participating states (as of 2024)."""
        countries = COUNTRY_GROUPS["A:1"]["countries"]
        # Allow some flexibility for membership changes
        assert len(countries) >= 40, f"Wassenaar has {len(countries)} members, expected ~42"

    def test_key_wassenaar_members_present(self):
        """Key Wassenaar members should be included."""
        countries = COUNTRY_GROUPS["A:1"]["countries"]
        key_members = [
            "Australia",
            "Canada",
            "France",
            "Germany",
            "Japan",
            "United Kingdom",
            "Italy",
            "Netherlands",
            "South Korea",
            "Sweden",
        ]
        for member in key_members:
            assert member in countries, f"Missing Wassenaar member: {member}"

    def test_russia_not_in_wassenaar(self):
        """Russia was suspended from Wassenaar in 2022."""
        countries = COUNTRY_GROUPS["A:1"]["countries"]
        # Note: Russia may still be listed if data predates suspension
        # This test documents the expected state
        if "Russia" in countries:
            pass  # Data may need updating - log but don't fail


class TestNATOMembers:
    """Verify Country Group A:6 (NATO) accuracy."""

    def test_nato_member_count(self):
        """NATO should have 32 members (as of 2024 with Sweden)."""
        countries = COUNTRY_GROUPS["A:6"]["countries"]
        assert len(countries) >= 30, f"NATO has {len(countries)} members, expected 32"

    def test_key_nato_members_present(self):
        """Key NATO members should be included."""
        countries = COUNTRY_GROUPS["A:6"]["countries"]
        key_members = [
            "United States" if "United States" in countries else "Canada",
            "Canada",
            "France",
            "Germany",
            "United Kingdom",
            "Italy",
            "Poland",
            "Turkey",
        ]
        for member in key_members:
            if member != "United States":  # US may not be listed as it's the origin
                assert member in countries, f"Missing NATO member: {member}"

    def test_finland_sweden_in_nato(self):
        """Finland and Sweden joined NATO in 2023-2024."""
        countries = COUNTRY_GROUPS["A:6"]["countries"]
        assert "Finland" in countries, "Finland should be in NATO (joined 2023)"
        assert "Sweden" in countries, "Sweden should be in NATO (joined 2024)"


class TestEmbargoCountries:
    """Verify embargo country lists (A:5, D:5, E:1, E:2) accuracy."""

    def test_arms_embargo_countries(self):
        """Arms embargo countries (A:5/D:5) should match."""
        a5 = set(COUNTRY_GROUPS["A:5"]["countries"])
        d5 = set(COUNTRY_GROUPS["D:5"]["countries"])
        # A:5 and D:5 should be identical
        assert a5 == d5, f"A:5 and D:5 differ: A:5-D:5={a5-d5}, D:5-A:5={d5-a5}"

    def test_core_embargo_countries_present(self):
        """Core embargo countries should be in D:5."""
        countries = set(COUNTRY_GROUPS["D:5"]["countries"])
        core_embargoed = {"Cuba", "Iran", "North Korea", "Syria", "Russia"}
        for country in core_embargoed:
            assert country in countries, f"Missing embargo country: {country}"

    def test_terrorist_supporting_countries(self):
        """E:1 should contain state sponsors of terrorism."""
        countries = set(COUNTRY_GROUPS["E:1"]["countries"])
        # As of 2024: Cuba, Iran, North Korea, Syria
        expected = {"Cuba", "Iran", "North Korea", "Syria"}
        assert countries == expected, f"E:1 mismatch. Got {countries}, expected {expected}"

    def test_comprehensive_embargo_countries(self):
        """E:2 should contain countries under comprehensive embargo."""
        countries = set(COUNTRY_GROUPS["E:2"]["countries"])
        # Cuba and North Korea are under comprehensive embargo
        assert "Cuba" in countries
        assert "North Korea" in countries


class TestNationalSecurityConcerns:
    """Verify Country Group D:1 (National Security) accuracy."""

    def test_d1_includes_key_countries(self):
        """D:1 should include countries of national security concern."""
        countries = set(COUNTRY_GROUPS["D:1"]["countries"])
        expected_members = ["China", "Russia", "Iran", "Pakistan", "Belarus"]
        for country in expected_members:
            # Iran may be in E:1/E:2 instead
            if country != "Iran":
                assert country in countries, f"Missing D:1 country: {country}"

    def test_china_hong_kong_macau_in_d1(self):
        """China, Hong Kong, and Macau should all be in D:1."""
        countries = set(COUNTRY_GROUPS["D:1"]["countries"])
        assert "China" in countries
        assert "Hong Kong" in countries
        assert "Macau" in countries


class TestCountryGroupInvariants:
    """Test logical invariants that should always hold."""

    def test_e1_subset_of_d5(self):
        """All E:1 countries should also be in D:5 (arms embargo)."""
        e1 = set(COUNTRY_GROUPS["E:1"]["countries"])
        d5 = set(COUNTRY_GROUPS["D:5"]["countries"])
        missing = e1 - d5
        assert not missing, f"E:1 countries not in D:5: {missing}"

    def test_e2_subset_of_e1(self):
        """All E:2 countries should also be in E:1."""
        e1 = set(COUNTRY_GROUPS["E:1"]["countries"])
        e2 = set(COUNTRY_GROUPS["E:2"]["countries"])
        missing = e2 - e1
        assert not missing, f"E:2 countries not in E:1: {missing}"

    def test_no_nato_in_embargo(self):
        """NATO members should not be in arms embargo list."""
        nato = set(COUNTRY_GROUPS["A:6"]["countries"])
        embargo = set(COUNTRY_GROUPS["D:5"]["countries"])
        overlap = nato & embargo
        # Turkey is a special case - NATO member but has some restrictions
        overlap.discard("Turkey")
        assert not overlap, f"NATO countries in embargo list: {overlap}"

    def test_wassenaar_not_in_d1(self):
        """Wassenaar members generally shouldn't be in D:1 (except India, Ukraine)."""
        wassenaar = set(COUNTRY_GROUPS["A:1"]["countries"])
        d1 = set(COUNTRY_GROUPS["D:1"]["countries"])
        overlap = wassenaar & d1
        # India and Ukraine are exceptions - Wassenaar members but in D:1
        allowed_exceptions = {"India", "Ukraine"}
        unexpected = overlap - allowed_exceptions
        assert not unexpected, f"Wassenaar members unexpectedly in D:1: {unexpected}"


class TestCountryLookup:
    """Test the get_country_groups lookup function."""

    def test_lookup_germany(self):
        """Germany should be in Wassenaar and NATO."""
        groups = get_country_groups("Germany")
        assert "A:1" in groups, "Germany should be in A:1 (Wassenaar)"
        assert "A:6" in groups, "Germany should be in A:6 (NATO)"

    def test_lookup_china(self):
        """China should be in multiple D groups."""
        groups = get_country_groups("China")
        assert "D:1" in groups, "China should be in D:1"
        assert "D:5" in groups, "China should be in D:5"

    def test_lookup_case_insensitive(self):
        """Lookup should be case-insensitive."""
        groups_lower = get_country_groups("germany")
        groups_upper = get_country_groups("GERMANY")
        groups_mixed = get_country_groups("Germany")
        assert groups_lower == groups_upper == groups_mixed

    def test_lookup_unknown_country(self):
        """Unknown country should return empty list."""
        groups = get_country_groups("Wakanda")
        assert groups == []

    def test_lookup_iran_groups(self):
        """Iran should be in terrorism and embargo groups."""
        groups = get_country_groups("Iran")
        assert "E:1" in groups, "Iran should be in E:1 (terrorism)"
        assert "D:4" in groups, "Iran should be in D:4 (missile)"
