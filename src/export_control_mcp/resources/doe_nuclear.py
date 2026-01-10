"""DOE Nuclear Export Control Reference Data.

This module contains reference data for DOE nuclear-related export controls:
- 10 CFR 810 (Assistance to Foreign Atomic Energy Activities)
- Generally Authorized Destinations (Appendix A)
- Specifically Authorized Countries (require case-by-case approval)
- Activity categories under 810.6

Sources:
- https://www.ecfr.gov/current/title-10/chapter-III/part-810
- https://www.energy.gov/nnsa/10-cfr-part-810
"""

from dataclasses import dataclass
from enum import Enum


class CFR810AuthorizationType(str, Enum):
    """Authorization type under 10 CFR 810."""

    GENERALLY_AUTHORIZED = "generally_authorized"
    SPECIFIC_AUTHORIZATION = "specific_authorization"
    PROHIBITED = "prohibited"


@dataclass
class CFR810Country:
    """Country classification under 10 CFR 810."""

    name: str
    iso_code: str
    authorization_type: CFR810AuthorizationType
    has_123_agreement: bool = False
    notes: str = ""


# Generally Authorized Destinations (10 CFR 810 Appendix A)
# These countries can receive certain nuclear technology assistance
# without specific DOE authorization (as of November 2025)
GENERALLY_AUTHORIZED_DESTINATIONS = [
    "Argentina",
    "Australia",
    "Austria",
    "Belgium",
    "Brazil",
    "Bulgaria",
    "Canada",
    "Chile",
    "Croatia",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Indonesia",
    "Ireland",
    "Italy",
    "Japan",
    "Kazakhstan",
    "Korea, Republic of",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Mexico",
    "Morocco",
    "Netherlands",
    "Norway",
    "Philippines",  # Added September 2025
    "Poland",
    "Portugal",
    "Romania",
    "Singapore",  # Added September 2025
    "Slovakia",
    "Slovenia",
    "South Africa",
    "Spain",
    "Sweden",
    "Switzerland",
    "Taiwan",
    "Turkey",
    "Ukraine",
    "United Arab Emirates",
    "United Kingdom",
    "Vietnam",
]

# Countries with 123 Agreements but NOT in Appendix A
# (require specific authorization for all Part 810 activities)
SPECIFIC_AUTHORIZATION_WITH_123 = {
    "China": {
        "has_123_agreement": True,
        "notes": "Has 123 Agreement but excluded from Appendix A due to policy concerns",
    },
    "Russia": {
        "has_123_agreement": True,
        "notes": "123 Agreement suspended; requires specific authorization",
    },
    "India": {
        "has_123_agreement": True,
        "notes": "Has 123 Agreement but not in Appendix A; specific authorization required",
    },
    "Egypt": {
        "has_123_agreement": True,
        "notes": "Has 123 Agreement but not in Appendix A",
    },
}

# Prohibited destinations (comprehensive sanctions or no nuclear cooperation)
PROHIBITED_DESTINATIONS = [
    "Cuba",
    "Iran",
    "North Korea",
    "Syria",
]

# ISO country code mapping for common lookups
COUNTRY_ISO_CODES = {
    "Argentina": "AR",
    "Australia": "AU",
    "Austria": "AT",
    "Belgium": "BE",
    "Brazil": "BR",
    "Bulgaria": "BG",
    "Canada": "CA",
    "Chile": "CL",
    "China": "CN",
    "Croatia": "HR",
    "Cuba": "CU",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Egypt": "EG",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "GR",
    "Hungary": "HU",
    "India": "IN",
    "Indonesia": "ID",
    "Iran": "IR",
    "Ireland": "IE",
    "Italy": "IT",
    "Japan": "JP",
    "Kazakhstan": "KZ",
    "Korea, Republic of": "KR",
    "South Korea": "KR",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Mexico": "MX",
    "Morocco": "MA",
    "Netherlands": "NL",
    "North Korea": "KP",
    "Norway": "NO",
    "Philippines": "PH",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Russia": "RU",
    "Singapore": "SG",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "South Africa": "ZA",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Syria": "SY",
    "Taiwan": "TW",
    "Turkey": "TR",
    "Ukraine": "UA",
    "United Arab Emirates": "AE",
    "United Kingdom": "GB",
    "Vietnam": "VN",
}


# Activities under 10 CFR 810.6 (Generally Authorized Activities)
# These activities are generally authorized to Appendix A countries
GENERALLY_AUTHORIZED_ACTIVITIES = {
    "810.6(a)": {
        "title": "Publicly Available Information",
        "description": "Furnishing publicly available information or information in the public domain",
        "requires_reporting": False,
    },
    "810.6(b)": {
        "title": "Enrichment Below 20%",
        "description": "Participation in exchange programs approved by DOE/NNSA",
        "requires_reporting": True,
    },
    "810.6(c)": {
        "title": "Nuclear Safety",
        "description": "Activities related to nuclear safety and safeguards",
        "requires_reporting": True,
    },
    "810.6(d)": {
        "title": "Radioisotope Production",
        "description": "Production of radioisotopes for medical, industrial, or research use",
        "requires_reporting": True,
    },
}

# Activities requiring Specific Authorization (10 CFR 810.7)
SPECIFIC_AUTHORIZATION_ACTIVITIES = {
    "sensitive_nuclear_technology": {
        "title": "Sensitive Nuclear Technology",
        "description": "Technology for uranium enrichment, nuclear fuel reprocessing, "
        "or production of heavy water",
        "always_requires_specific": True,
    },
    "enrichment_technology": {
        "title": "Uranium Enrichment Technology",
        "description": "Any technology related to uranium isotope separation",
        "always_requires_specific": True,
    },
    "reprocessing_technology": {
        "title": "Reprocessing Technology",
        "description": "Technology for separating plutonium or uranium-233 from irradiated fuel",
        "always_requires_specific": True,
    },
    "heavy_water_production": {
        "title": "Heavy Water Production",
        "description": "Technology for production of heavy water (deuterium oxide)",
        "always_requires_specific": True,
    },
    "non_appendix_a_destination": {
        "title": "Non-Appendix A Destination",
        "description": "Any nuclear assistance to countries not listed in Appendix A",
        "always_requires_specific": True,
    },
}


def get_cfr810_authorization(country: str) -> CFR810Country | None:
    """
    Determine 10 CFR 810 authorization status for a country.

    Args:
        country: Country name (case-insensitive)

    Returns:
        CFR810Country with authorization details, or None if not found
    """
    country_normalized = country.strip()

    # Handle common variations
    country_map = {
        "south korea": "Korea, Republic of",
        "republic of korea": "Korea, Republic of",
        "rok": "Korea, Republic of",
        "uae": "United Arab Emirates",
        "uk": "United Kingdom",
        "great britain": "United Kingdom",
        "dprk": "North Korea",
    }

    country_lower = country_normalized.lower()
    if country_lower in country_map:
        country_normalized = country_map[country_lower]

    # Check Generally Authorized
    for dest in GENERALLY_AUTHORIZED_DESTINATIONS:
        if dest.lower() == country_normalized.lower():
            return CFR810Country(
                name=dest,
                iso_code=COUNTRY_ISO_CODES.get(dest, ""),
                authorization_type=CFR810AuthorizationType.GENERALLY_AUTHORIZED,
                has_123_agreement=True,
                notes="Listed in Appendix A to 10 CFR 810",
            )

    # Check Prohibited
    for dest in PROHIBITED_DESTINATIONS:
        if dest.lower() == country_normalized.lower():
            return CFR810Country(
                name=dest,
                iso_code=COUNTRY_ISO_CODES.get(dest, ""),
                authorization_type=CFR810AuthorizationType.PROHIBITED,
                has_123_agreement=False,
                notes="Subject to comprehensive sanctions; nuclear assistance prohibited",
            )

    # Check Specific Authorization with 123 Agreement
    for dest, info in SPECIFIC_AUTHORIZATION_WITH_123.items():
        if dest.lower() == country_normalized.lower():
            return CFR810Country(
                name=dest,
                iso_code=COUNTRY_ISO_CODES.get(dest, ""),
                authorization_type=CFR810AuthorizationType.SPECIFIC_AUTHORIZATION,
                has_123_agreement=info["has_123_agreement"],
                notes=info["notes"],
            )

    # Default: Specific authorization required (not in Appendix A)
    iso = COUNTRY_ISO_CODES.get(country_normalized, "")
    if iso or len(country_normalized) >= 3:  # Likely a valid country
        return CFR810Country(
            name=country_normalized,
            iso_code=iso,
            authorization_type=CFR810AuthorizationType.SPECIFIC_AUTHORIZATION,
            has_123_agreement=False,
            notes="Not in Appendix A; specific DOE authorization required for Part 810 activities",
        )

    return None


def is_generally_authorized(country: str) -> bool:
    """
    Check if a country is a Generally Authorized Destination under 10 CFR 810.

    Args:
        country: Country name

    Returns:
        True if country is in Appendix A (Generally Authorized)
    """
    result = get_cfr810_authorization(country)
    return (
        result is not None
        and result.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED
    )


def is_prohibited_destination(country: str) -> bool:
    """
    Check if a country is prohibited for nuclear assistance.

    Args:
        country: Country name

    Returns:
        True if country is prohibited
    """
    result = get_cfr810_authorization(country)
    return result is not None and result.authorization_type == CFR810AuthorizationType.PROHIBITED


def get_all_generally_authorized() -> list[str]:
    """Return list of all Generally Authorized Destinations."""
    return GENERALLY_AUTHORIZED_DESTINATIONS.copy()


def get_all_prohibited() -> list[str]:
    """Return list of all prohibited destinations."""
    return PROHIBITED_DESTINATIONS.copy()


# Part 810 Guidance for National Labs
NATIONAL_LAB_GUIDANCE = {
    "tcp_required": {
        "title": "Technology Control Plan Required",
        "description": "A TCP may be required when providing nuclear technology assistance "
        "to foreign nationals, even for Generally Authorized destinations",
        "applies_to": ["deemed exports", "foreign visits", "foreign assignments"],
    },
    "reporting_requirements": {
        "title": "Reporting Requirements",
        "description": "Most Part 810 activities require reporting to DOE/NNSA, "
        "even when generally authorized",
        "forms": ["DOE F 810.1", "DOE F 810.2"],
    },
    "fundamental_research": {
        "title": "Fundamental Research Exclusion",
        "description": "Basic research in nuclear science that will be published "
        "and shared broadly may be excluded from Part 810 requirements",
        "conditions": [
            "Research is fundamental (basic science)",
            "Results will be published without restriction",
            "No proprietary or national security restrictions",
        ],
    },
    "coordination": {
        "title": "Lab Export Control Office Coordination",
        "description": "All Part 810 activities should be coordinated with the "
        "laboratory's export control office before initiation",
        "contacts": "Contact your institution's Export Control Officer",
    },
}
