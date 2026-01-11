"""Data validation tests for ECCN and USML reference data.

These tests verify that ECCN data matches the Commerce Control List (15 CFR 774)
and USML data matches the Munitions List (22 CFR 121).
"""

from export_control_mcp.resources.reference_data import (
    CONTROL_REASONS,
    ECCN_DATA,
    LICENSE_EXCEPTIONS,
    USML_CATEGORIES,
    get_eccn,
    get_usml_category,
)


class TestECCNDataStructure:
    """Verify ECCN data structure completeness."""

    def test_eccn_entries_have_required_fields(self):
        """Each ECCN entry should have title, description, control_reasons."""
        for eccn, data in ECCN_DATA.items():
            assert "title" in data, f"{eccn} missing 'title'"
            assert "description" in data, f"{eccn} missing 'description'"
            assert "control_reasons" in data, f"{eccn} missing 'control_reasons'"
            assert "license_exceptions" in data, f"{eccn} missing 'license_exceptions'"

    def test_control_reasons_are_valid(self):
        """All control reasons should be valid codes."""
        valid_reasons = set(CONTROL_REASONS.keys())
        for eccn, data in ECCN_DATA.items():
            for reason in data.get("control_reasons", []):
                assert reason in valid_reasons, f"{eccn} has invalid reason: {reason}"

    def test_license_exceptions_are_valid(self):
        """All license exceptions should be valid codes."""
        valid_exceptions = set(LICENSE_EXCEPTIONS.keys())
        # Add common exceptions that may not be in our reference
        valid_exceptions.update({"APP", "ACE", "AGR", "KMI", "NAC", "NON"})
        for eccn, data in ECCN_DATA.items():
            for exc in data.get("license_exceptions", []):
                assert exc in valid_exceptions, f"{eccn} has invalid exception: {exc}"


class TestECCNFormatValidation:
    """Verify ECCN format follows CCL structure."""

    def test_eccn_format_valid(self):
        """All ECCNs should follow #X### format."""
        import re

        pattern = r"^[0-9][A-E][0-9]{3}$"
        for eccn in ECCN_DATA:
            assert re.match(pattern, eccn), f"Invalid ECCN format: {eccn}"

    def test_eccn_categories_valid(self):
        """ECCN category (first digit) should be 0-9."""
        for eccn in ECCN_DATA:
            category = int(eccn[0])
            assert 0 <= category <= 9, f"Invalid category in {eccn}"

    def test_eccn_product_groups_valid(self):
        """ECCN product group (second char) should be A-E."""
        valid_groups = {"A", "B", "C", "D", "E"}
        for eccn in ECCN_DATA:
            group = eccn[1]
            assert group in valid_groups, f"Invalid product group in {eccn}: {group}"


class TestECCNContentAccuracy:
    """Verify specific ECCN content is accurate."""

    def test_3a001_is_electronics(self):
        """3A001 should be electronic components."""
        data = ECCN_DATA.get("3A001")
        assert data is not None, "3A001 should exist"
        assert "electronic" in data["title"].lower()

    def test_5a002_is_encryption(self):
        """5A002 should be information security/encryption."""
        data = ECCN_DATA.get("5A002")
        assert data is not None, "5A002 should exist"
        assert "information security" in data["title"].lower() or "security" in data["title"].lower()
        assert "EI" in data["control_reasons"], "5A002 should have EI control reason"

    def test_9a004_is_spacecraft(self):
        """9A004 should be spacecraft/launch vehicles."""
        data = ECCN_DATA.get("9A004")
        assert data is not None, "9A004 should exist"
        assert "space" in data["title"].lower() or "spacecraft" in data["title"].lower()

    def test_encryption_items_have_enc_exception(self):
        """Encryption commodities and software should have ENC license exception."""
        # Note: 5E002 (technology) uses TSR, not ENC per 15 CFR 740.17
        encryption_eccns = ["5A002", "5D002"]
        for eccn in encryption_eccns:
            data = ECCN_DATA.get(eccn)
            if data:
                assert "ENC" in data.get(
                    "license_exceptions", []
                ), f"{eccn} should have ENC exception"


class TestECCNLookupFunction:
    """Test the get_eccn lookup function."""

    def test_lookup_valid_eccn(self):
        """Should return ECCN object for valid ECCN."""
        result = get_eccn("3A001")
        assert result is not None
        assert result.raw == "3A001"
        assert result.category == 3
        assert result.product_group == "A"

    def test_lookup_populates_data(self):
        """Should populate title and control reasons from reference data."""
        result = get_eccn("3A001")
        assert result is not None
        assert result.title != ""
        assert len(result.control_reasons) > 0

    def test_lookup_case_insensitive(self):
        """Lookup should handle different cases."""
        result = get_eccn("3a001")
        assert result is not None
        assert result.raw == "3A001"

    def test_lookup_invalid_format(self):
        """Should return None for invalid ECCN format."""
        result = get_eccn("INVALID")
        assert result is None

    def test_lookup_unknown_eccn(self):
        """Should return parsed ECCN even if not in reference data."""
        result = get_eccn("0A000")  # Valid format but not in our sample data
        assert result is not None
        assert result.category == 0
        assert result.product_group == "A"


class TestUSMLCategoryStructure:
    """Verify USML category data structure."""

    def test_all_21_categories_exist(self):
        """All 21 USML categories should be defined."""
        for i in range(1, 22):
            assert i in USML_CATEGORIES, f"Missing USML Category {i}"

    def test_categories_have_required_fields(self):
        """Each category should have title, description, sme flag, and items."""
        for cat_num, data in USML_CATEGORIES.items():
            assert "title" in data, f"Category {cat_num} missing 'title'"
            assert "description" in data, f"Category {cat_num} missing 'description'"
            assert "sme" in data, f"Category {cat_num} missing 'sme' flag"
            assert "items" in data, f"Category {cat_num} missing 'items'"

    def test_sme_flag_is_boolean(self):
        """SME (Significant Military Equipment) flag should be boolean."""
        for cat_num, data in USML_CATEGORIES.items():
            assert isinstance(data["sme"], bool), f"Category {cat_num} SME should be boolean"


class TestUSMLCategoryAccuracy:
    """Verify specific USML category content."""

    def test_category_1_is_firearms(self):
        """Category I should be firearms."""
        data = USML_CATEGORIES.get(1)
        assert data is not None
        assert "firearm" in data["title"].lower()

    def test_category_4_is_missiles(self):
        """Category IV should be missiles/launch vehicles."""
        data = USML_CATEGORIES.get(4)
        assert data is not None
        assert "missile" in data["title"].lower() or "launch" in data["title"].lower()

    def test_category_8_is_aircraft(self):
        """Category VIII should be aircraft."""
        data = USML_CATEGORIES.get(8)
        assert data is not None
        assert "aircraft" in data["title"].lower()

    def test_category_11_is_electronics(self):
        """Category XI should be military electronics."""
        data = USML_CATEGORIES.get(11)
        assert data is not None
        assert "electronic" in data["title"].lower()

    def test_category_15_is_spacecraft(self):
        """Category XV should be spacecraft."""
        data = USML_CATEGORIES.get(15)
        assert data is not None
        assert "spacecraft" in data["title"].lower()

    def test_category_16_is_nuclear(self):
        """Category XVI should be nuclear weapons."""
        data = USML_CATEGORIES.get(16)
        assert data is not None
        assert "nuclear" in data["title"].lower()

    def test_weapons_categories_are_sme(self):
        """Weapons categories should be marked as SME."""
        weapons_categories = [1, 2, 3, 4, 5, 14, 16, 18]  # Firearms, guns, ammo, missiles, etc.
        for cat in weapons_categories:
            data = USML_CATEGORIES.get(cat)
            if data:
                assert data["sme"] is True, f"Category {cat} should be SME"


class TestUSMLLookupFunction:
    """Test the get_usml_category lookup function."""

    def test_lookup_by_number(self):
        """Should find category by Arabic numeral."""
        result = get_usml_category(1)
        assert result is not None
        assert result.number_arabic == 1

    def test_lookup_by_roman_numeral(self):
        """Should find category by Roman numeral."""
        result = get_usml_category("I")
        assert result is not None
        assert result.number_arabic == 1

    def test_lookup_populates_data(self):
        """Should populate title and items from reference data."""
        result = get_usml_category(1)
        assert result is not None
        assert result.title != ""
        assert len(result.items) > 0

    def test_lookup_invalid_category(self):
        """Should return None for invalid category number."""
        result = get_usml_category(99)
        assert result is None

    def test_lookup_string_number(self):
        """Should handle string numbers."""
        result = get_usml_category("8")
        assert result is not None
        assert result.number_arabic == 8


class TestControlReasons:
    """Verify control reason codes are complete."""

    def test_required_control_reasons_exist(self):
        """All standard control reason codes should be defined."""
        required = ["AT", "CB", "CC", "CW", "EI", "FC", "MT", "NS", "NP", "RS", "SS", "UN"]
        for code in required:
            assert code in CONTROL_REASONS, f"Missing control reason: {code}"

    def test_control_reasons_have_descriptions(self):
        """Each control reason should have a description."""
        for code, description in CONTROL_REASONS.items():
            assert isinstance(description, str), f"{code} description should be string"
            assert len(description) > 0, f"{code} has empty description"


class TestLicenseExceptions:
    """Verify license exception data."""

    def test_common_exceptions_exist(self):
        """Common license exceptions should be defined."""
        common = ["LVS", "GBS", "TMP", "RPL", "GOV", "TSU", "ENC", "STA"]
        for exc in common:
            assert exc in LICENSE_EXCEPTIONS, f"Missing license exception: {exc}"

    def test_exceptions_have_required_fields(self):
        """Each exception should have name, description, and CFR reference."""
        for code, data in LICENSE_EXCEPTIONS.items():
            assert "name" in data, f"{code} missing 'name'"
            assert "description" in data, f"{code} missing 'description'"
            assert "cfr" in data, f"{code} missing 'cfr'"

    def test_cfr_references_valid(self):
        """CFR references should follow 15 CFR 740.X format."""
        for code, data in LICENSE_EXCEPTIONS.items():
            cfr = data.get("cfr", "")
            assert cfr.startswith("15 CFR 740."), f"{code} has invalid CFR: {cfr}"
