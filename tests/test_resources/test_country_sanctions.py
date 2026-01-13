"""Tests for the country sanctions data loader module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from export_control_mcp.resources.country_sanctions import (
    _DATA_FILE,
    _load_country_sanctions_data,
    get_country_by_name,
    get_country_sanctions,
    get_country_sanctions_data,
    reload_country_sanctions_data,
)


class TestLoadCountrySanctionsData:
    """Tests for loading country sanctions data from JSON."""

    def test_should_load_data_from_json_file(self) -> None:
        """Test that data is loaded from the JSON file."""
        # Act
        data = _load_country_sanctions_data()

        # Assert
        assert len(data) > 0
        assert "IR" in data
        assert "RU" in data
        assert "CN" in data

    def test_should_return_country_sanctions_objects(self) -> None:
        """Test that loaded data contains CountrySanctions objects."""
        # Act
        data = _load_country_sanctions_data()

        # Assert
        iran = data.get("IR")
        assert iran is not None
        assert iran.country_code == "IR"
        assert iran.country_name == "Iran"
        assert "IRAN" in iran.ofac_programs
        assert iran.embargo_type == "comprehensive"
        assert iran.itar_restricted is True

    def test_should_return_empty_dict_when_file_not_found(self) -> None:
        """Test that empty dict is returned when file doesn't exist."""
        # Arrange
        with patch(
            "export_control_mcp.resources.country_sanctions._DATA_FILE",
            Path("/nonexistent/path.json"),
        ):
            # Act
            data = _load_country_sanctions_data()

            # Assert
            assert data == {}

    def test_should_handle_invalid_json_gracefully(self) -> None:
        """Test that invalid JSON returns empty dict."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)

        try:
            with patch(
                "export_control_mcp.resources.country_sanctions._DATA_FILE",
                temp_path,
            ):
                # Act
                data = _load_country_sanctions_data()

                # Assert
                assert data == {}
        finally:
            temp_path.unlink()

    def test_should_skip_countries_with_invalid_data(self) -> None:
        """Test that countries with invalid data are skipped."""
        # Arrange
        json_data = {
            "countries": {
                "XX": {"invalid": "data"},  # Missing required fields
                "YY": {
                    "country_code": "YY",
                    "country_name": "Valid Country",
                },
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = Path(f.name)

        try:
            with patch(
                "export_control_mcp.resources.country_sanctions._DATA_FILE",
                temp_path,
            ):
                # Act
                data = _load_country_sanctions_data()

                # Assert
                # YY should be loaded, XX should be skipped
                assert "YY" in data
                assert "XX" not in data
        finally:
            temp_path.unlink()


class TestGetCountrySanctionsData:
    """Tests for cached data access."""

    def test_should_return_cached_data(self) -> None:
        """Test that data is cached and returned consistently."""
        # Act
        data1 = get_country_sanctions_data()
        data2 = get_country_sanctions_data()

        # Assert
        assert data1 is data2  # Same object (cached)

    def test_should_contain_expected_countries(self) -> None:
        """Test that expected countries are in the data."""
        # Act
        data = get_country_sanctions_data()

        # Assert
        expected_countries = ["IR", "KP", "CU", "SY", "RU", "BY", "CN", "VE", "DE", "JP"]
        for code in expected_countries:
            assert code in data, f"Missing country: {code}"


class TestGetCountrySanctions:
    """Tests for getting sanctions by country code."""

    def test_should_return_sanctions_for_valid_code(self) -> None:
        """Test that sanctions are returned for valid code."""
        # Act
        result = get_country_sanctions("IR")

        # Assert
        assert result is not None
        assert result.country_code == "IR"
        assert result.country_name == "Iran"

    def test_should_handle_lowercase_code(self) -> None:
        """Test that lowercase codes are normalized."""
        # Act
        result = get_country_sanctions("ir")

        # Assert
        assert result is not None
        assert result.country_code == "IR"

    def test_should_return_none_for_unknown_code(self) -> None:
        """Test that None is returned for unknown country."""
        # Act
        result = get_country_sanctions("XX")

        # Assert
        assert result is None


class TestGetCountryByName:
    """Tests for getting sanctions by country name."""

    def test_should_find_country_by_exact_name(self) -> None:
        """Test finding country by exact name."""
        # Act
        result = get_country_by_name("Iran")

        # Assert
        assert result is not None
        assert result.country_code == "IR"

    def test_should_find_country_by_partial_name(self) -> None:
        """Test finding country by partial name match."""
        # Act
        result = get_country_by_name("North")

        # Assert
        assert result is not None
        assert result.country_code == "KP"

    def test_should_be_case_insensitive(self) -> None:
        """Test that search is case-insensitive."""
        # Act
        result = get_country_by_name("RUSSIA")

        # Assert
        assert result is not None
        assert result.country_code == "RU"

    def test_should_return_none_for_unknown_name(self) -> None:
        """Test that None is returned for unknown country."""
        # Act
        result = get_country_by_name("Unknownland")

        # Assert
        assert result is None


class TestReloadCountrySanctionsData:
    """Tests for cache clearing and reload."""

    def test_should_clear_cache_and_reload(self) -> None:
        """Test that cache is cleared and data reloaded."""
        # Arrange - get initial data
        initial_data = get_country_sanctions_data()

        # Act - reload
        reload_country_sanctions_data()
        reloaded_data = get_country_sanctions_data()

        # Assert - should have same content but potentially new object
        assert len(reloaded_data) == len(initial_data)
        assert "IR" in reloaded_data


class TestDataFileExists:
    """Tests for data file existence."""

    def test_data_file_should_exist(self) -> None:
        """Test that the JSON data file exists."""
        assert _DATA_FILE.exists(), f"Data file not found: {_DATA_FILE}"

    def test_data_file_should_be_valid_json(self) -> None:
        """Test that the data file is valid JSON."""
        with open(_DATA_FILE) as f:
            data = json.load(f)

        assert "countries" in data
        assert len(data["countries"]) > 0


class TestCountrySanctionsDataIntegrity:
    """Tests for data integrity and completeness."""

    def test_comprehensive_embargo_countries_should_have_itar_restricted(self) -> None:
        """Test that comprehensive embargo countries are ITAR restricted."""
        # Arrange
        data = get_country_sanctions_data()

        # Act & Assert
        for code, sanctions in data.items():
            if sanctions.embargo_type == "comprehensive":
                assert sanctions.itar_restricted, (
                    f"{code} has comprehensive embargo but itar_restricted=False"
                )

    def test_all_countries_should_have_summary(self) -> None:
        """Test that all countries have a summary."""
        # Arrange
        data = get_country_sanctions_data()

        # Act & Assert
        for code, sanctions in data.items():
            assert sanctions.summary, f"{code} missing summary"

    def test_sanctioned_countries_should_have_ofac_programs(self) -> None:
        """Test that sanctioned countries have OFAC programs."""
        # Arrange
        data = get_country_sanctions_data()
        sanctioned_codes = ["IR", "KP", "CU", "SY", "RU"]

        # Act & Assert
        for code in sanctioned_codes:
            sanctions = data.get(code)
            assert sanctions is not None
            assert len(sanctions.ofac_programs) > 0, f"{code} missing OFAC programs"
