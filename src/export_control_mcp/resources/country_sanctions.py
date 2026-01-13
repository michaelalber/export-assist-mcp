"""Country sanctions data loader.

Loads country-level sanctions and export control data from JSON configuration.
This separates data from code, making updates easier without code changes.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

from export_control_mcp.models.sanctions import CountrySanctions

logger = logging.getLogger(__name__)

# Path to the JSON data file
_DATA_FILE = Path(__file__).parent / "data" / "country_sanctions.json"


def _load_country_sanctions_data() -> dict[str, CountrySanctions]:
    """
    Load country sanctions data from JSON file.

    Returns:
        Dictionary mapping country codes to CountrySanctions objects.
    """
    if not _DATA_FILE.exists():
        logger.warning(f"Country sanctions data file not found: {_DATA_FILE}")
        return {}

    try:
        with open(_DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)

        countries_data = data.get("countries", {})
        result = {}

        for code, country_data in countries_data.items():
            try:
                result[code] = CountrySanctions(
                    country_code=country_data["country_code"],
                    country_name=country_data["country_name"],
                    ofac_programs=country_data.get("ofac_programs", []),
                    embargo_type=country_data.get("embargo_type", "none"),
                    ear_country_groups=country_data.get("ear_country_groups", []),
                    itar_restricted=country_data.get("itar_restricted", False),
                    arms_embargo=country_data.get("arms_embargo", False),
                    summary=country_data.get("summary", ""),
                    key_restrictions=country_data.get("key_restrictions", []),
                    notes=country_data.get("notes", []),
                )
            except Exception as e:
                logger.warning(f"Error loading country {code}: {e}")
                continue

        logger.info(f"Loaded {len(result)} country sanctions profiles")
        return result

    except Exception as e:
        logger.error(f"Failed to load country sanctions data: {e}")
        return {}


@lru_cache(maxsize=1)
def get_country_sanctions_data() -> dict[str, CountrySanctions]:
    """
    Get cached country sanctions data.

    Uses lru_cache to load data only once per process.

    Returns:
        Dictionary mapping country codes to CountrySanctions objects.
    """
    return _load_country_sanctions_data()


def get_country_sanctions(country_code: str) -> CountrySanctions | None:
    """
    Get sanctions data for a specific country by code.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., "IR", "RU").

    Returns:
        CountrySanctions object if found, None otherwise.
    """
    data = get_country_sanctions_data()
    return data.get(country_code.upper())


def get_country_by_name(name: str) -> CountrySanctions | None:
    """
    Get sanctions data for a country by name (partial match).

    Args:
        name: Country name or partial name.

    Returns:
        CountrySanctions object if found, None otherwise.
    """
    data = get_country_sanctions_data()
    name_lower = name.lower()

    for sanctions in data.values():
        if name_lower in sanctions.country_name.lower():
            return sanctions

    return None


def reload_country_sanctions_data() -> None:
    """
    Clear the cache and reload country sanctions data.

    Call this after updating the JSON file to pick up changes.
    """
    get_country_sanctions_data.cache_clear()
    # Pre-load to verify data is valid
    get_country_sanctions_data()
