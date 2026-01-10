"""Sanctions list search tools for Export Control MCP.

Provides search capabilities for BIS Entity List, OFAC SDN List,
Denied Persons List, and country-level sanctions information.
"""

from export_control_mcp.audit import audit_log
from export_control_mcp.models.sanctions import (
    CountrySanctions,
    EntityType,
)
from export_control_mcp.server import mcp
from export_control_mcp.services import get_sanctions_db


# Country sanctions data (preloaded for common queries)
COUNTRY_SANCTIONS_DATA: dict[str, CountrySanctions] = {
    "IR": CountrySanctions(
        country_code="IR",
        country_name="Iran",
        ofac_programs=["IRAN", "IRAN-TRA", "IRAN-HR", "IFSR", "IRGC"],
        embargo_type="comprehensive",
        ear_country_groups=["D:1", "D:3", "D:4", "E:1"],
        itar_restricted=True,
        arms_embargo=True,
        summary="Iran is subject to comprehensive U.S. sanctions administered by OFAC and extensive export controls under EAR and ITAR.",
        key_restrictions=[
            "Virtually all exports and reexports require a license",
            "License applications generally denied under policy of denial",
            "ITAR proscribed destination - no defense articles or services",
            "Financial transactions heavily restricted",
        ],
        notes=[
            "Some humanitarian exceptions may apply",
            "Iran Human Rights sanctions target specific officials",
        ],
    ),
    "KP": CountrySanctions(
        country_code="KP",
        country_name="North Korea",
        ofac_programs=["DPRK", "DPRK2", "DPRK3", "DPRK4"],
        embargo_type="comprehensive",
        ear_country_groups=["D:1", "D:3", "D:4", "E:1"],
        itar_restricted=True,
        arms_embargo=True,
        summary="North Korea (DPRK) is subject to the most restrictive U.S. sanctions regime.",
        key_restrictions=[
            "Complete trade embargo",
            "All EAR-controlled items require license (presumption of denial)",
            "ITAR proscribed destination",
            "UN sanctions also apply",
        ],
        notes=["Limited humanitarian exceptions"],
    ),
    "CU": CountrySanctions(
        country_code="CU",
        country_name="Cuba",
        ofac_programs=["CUBA"],
        embargo_type="comprehensive",
        ear_country_groups=["D:1", "E:1", "E:2"],
        itar_restricted=True,
        arms_embargo=True,
        summary="Cuba is subject to comprehensive U.S. economic sanctions under the Cuban embargo.",
        key_restrictions=[
            "General prohibition on trade and financial transactions",
            "Export controls under both EAR and OFAC regulations",
            "ITAR proscribed destination",
        ],
        notes=[
            "Some people-to-people travel exceptions",
            "Certain telecom equipment exceptions available",
        ],
    ),
    "SY": CountrySanctions(
        country_code="SY",
        country_name="Syria",
        ofac_programs=["SYRIA"],
        embargo_type="comprehensive",
        ear_country_groups=["D:1", "D:3", "E:1"],
        itar_restricted=True,
        arms_embargo=True,
        summary="Syria is subject to comprehensive U.S. sanctions including the Syria Accountability Act.",
        key_restrictions=[
            "Broad prohibition on exports",
            "License requirements for most items",
            "ITAR proscribed destination",
            "Designated pursuant to multiple sanctions programs",
        ],
        notes=["Limited humanitarian exceptions may apply"],
    ),
    "RU": CountrySanctions(
        country_code="RU",
        country_name="Russia",
        ofac_programs=["RUSSIA-EO14024", "UKRAINE-EO13660", "RUSSIA"],
        embargo_type="targeted",
        ear_country_groups=["D:1", "D:4", "D:5"],
        itar_restricted=True,
        arms_embargo=True,
        summary="Russia is subject to extensive targeted sanctions and export controls following its invasion of Ukraine.",
        key_restrictions=[
            "Comprehensive export controls on technology, especially semiconductors",
            "Entity List designations for hundreds of Russian entities",
            "SDN designations for Russian government officials and oligarchs",
            "Restrictions on luxury goods",
            "ITAR proscribed destination",
        ],
        notes=[
            "Sanctions regime has expanded significantly since February 2022",
            "Industry-specific guidance available from BIS and OFAC",
        ],
    ),
    "BY": CountrySanctions(
        country_code="BY",
        country_name="Belarus",
        ofac_programs=["BELARUS"],
        embargo_type="targeted",
        ear_country_groups=["D:1", "D:4"],
        itar_restricted=True,
        arms_embargo=True,
        summary="Belarus is subject to extensive targeted sanctions due to support for Russia's actions in Ukraine.",
        key_restrictions=[
            "Export controls aligned with Russia restrictions",
            "SDN designations for Lukashenko regime officials",
            "Technology restrictions similar to Russia",
        ],
        notes=["Sanctions expanded in coordination with Russia measures"],
    ),
    "CN": CountrySanctions(
        country_code="CN",
        country_name="China",
        ofac_programs=["CMIC", "NS-CMIC"],
        embargo_type="targeted",
        ear_country_groups=["D:1", "D:3", "D:4", "D:5"],
        itar_restricted=False,
        arms_embargo=True,
        summary="China is subject to targeted export controls, especially on advanced technology, and growing sanctions.",
        key_restrictions=[
            "Strict controls on advanced semiconductors and chip manufacturing equipment",
            "Entity List includes many Chinese companies (Huawei, SMIC, etc.)",
            "Military End-User controls (MEU List)",
            "U.S. arms embargo since 1989",
        ],
        notes=[
            "Not an ITAR proscribed country, but significant restrictions",
            "Controls tightening on AI and quantum technology",
        ],
    ),
    "VE": CountrySanctions(
        country_code="VE",
        country_name="Venezuela",
        ofac_programs=["VENEZUELA", "VENEZUELA-EO13692"],
        embargo_type="targeted",
        ear_country_groups=["D:1", "D:4"],
        itar_restricted=False,
        arms_embargo=True,
        summary="Venezuela is subject to targeted sanctions on the oil sector and government officials.",
        key_restrictions=[
            "Oil sector restrictions (PDVSA)",
            "SDN designations for Maduro regime officials",
            "Financial restrictions",
        ],
        notes=["Some general licenses available for certain activities"],
    ),
    "DE": CountrySanctions(
        country_code="DE",
        country_name="Germany",
        ofac_programs=[],
        embargo_type="none",
        ear_country_groups=["A:1", "A:5", "B"],
        itar_restricted=False,
        arms_embargo=False,
        summary="Germany is a close U.S. ally with favorable export control treatment.",
        key_restrictions=[
            "Most commercial exports permitted under license exceptions",
            "Some items may require license based on ECCN",
        ],
        notes=["NATO ally with defense trade cooperation agreements"],
    ),
    "JP": CountrySanctions(
        country_code="JP",
        country_name="Japan",
        ofac_programs=[],
        embargo_type="none",
        ear_country_groups=["A:1", "A:5", "B"],
        itar_restricted=False,
        arms_embargo=False,
        summary="Japan is a close U.S. ally with favorable export control treatment.",
        key_restrictions=[
            "Most commercial exports permitted under license exceptions",
        ],
        notes=["Treaty ally with extensive defense trade cooperation"],
    ),
}


def _initialize_country_sanctions() -> None:
    """Initialize country sanctions data in the database."""
    db = get_sanctions_db()
    for sanctions in COUNTRY_SANCTIONS_DATA.values():
        db.add_country_sanctions(sanctions)


@mcp.tool()
@audit_log
async def search_entity_list(
    query: str,
    country: str | None = None,
    fuzzy_threshold: float = 0.7,
    limit: int = 20,
) -> list[dict]:
    """
    Search the BIS Entity List for parties subject to export restrictions.

    The Entity List (Supplement No. 4 to Part 744 of the EAR) identifies
    entities for which there is reasonable cause to believe they have been
    involved in activities contrary to U.S. national security or foreign
    policy interests.

    Exports to Entity List parties require a license, and applications are
    typically subject to a policy of denial.

    Args:
        query: Name or partial name to search for. Supports fuzzy matching
               to catch name variations and transliterations.
               Examples:
               - "Huawei"
               - "SMIC"
               - "Moscow Institute"
        country: Optional two-letter country code to filter results.
                 Examples: "CN" (China), "RU" (Russia), "IR" (Iran)
        fuzzy_threshold: Minimum match score (0-1) for fuzzy matches.
                        Lower values return more results but may include
                        false positives. Default 0.7 (70% match).
        limit: Maximum number of results to return (1-100, default 20).

    Returns:
        List of matching entries, each containing:
        - entry: Entity details (name, aliases, addresses, country, etc.)
        - match_score: Fuzzy match score (0-1, higher is better)
        - match_type: How the match was found (exact, fuzzy_name, alias)
        - matched_field: Which field matched (name, alias)
        - matched_value: The actual value that matched

    Note:
        Always verify matches manually - fuzzy matching may produce false
        positives. For compliance decisions, confirm with official BIS sources.
    """
    db = get_sanctions_db()

    # Clamp parameters
    fuzzy_threshold = max(0.0, min(1.0, fuzzy_threshold))
    limit = max(1, min(100, limit))

    results = db.search_entity_list(
        query=query,
        country=country,
        fuzzy_threshold=fuzzy_threshold,
        limit=limit,
    )

    return [r.to_dict() for r in results]


@mcp.tool()
@audit_log
async def search_sdn_list(
    query: str,
    entity_type: str | None = None,
    program: str | None = None,
    fuzzy_threshold: float = 0.7,
    limit: int = 20,
) -> list[dict]:
    """
    Search the OFAC Specially Designated Nationals (SDN) List.

    The SDN List contains individuals and entities owned or controlled by,
    or acting for or on behalf of, targeted countries. It also lists
    individuals, groups, and entities designated under various sanctions
    programs (terrorism, narcotics trafficking, WMD proliferation, etc.).

    U.S. persons are generally prohibited from dealing with SDN-listed parties,
    and their assets within U.S. jurisdiction are blocked.

    Args:
        query: Name or partial name to search for. Supports fuzzy matching.
               Examples:
               - "BANK MELLI"
               - "Russian Direct Investment Fund"
               - Individual names like "DERIPASKA"
        entity_type: Optional filter by type. Options:
                    - "individual" - Natural persons
                    - "entity" - Companies, organizations
                    - "vessel" - Ships
                    - "aircraft" - Aircraft
        program: Optional filter by sanctions program. Examples:
                - "SDGT" - Specially Designated Global Terrorist
                - "IRAN" - Iran sanctions
                - "RUSSIA" - Russia-related sanctions
                - "DPRK" - North Korea sanctions
                - "VENEZUELA" - Venezuela sanctions
        fuzzy_threshold: Minimum match score (0-1) for fuzzy matches.
                        Default 0.7 (70% match).
        limit: Maximum number of results to return (1-100, default 20).

    Returns:
        List of matching entries, each containing:
        - entry: SDN details (name, type, programs, aliases, IDs, etc.)
        - match_score: Fuzzy match score (0-1)
        - match_type: How the match was found
        - matched_field: Which field matched
        - matched_value: The actual value that matched
    """
    db = get_sanctions_db()

    # Parse entity type
    sdn_type = None
    if entity_type:
        try:
            sdn_type = EntityType(entity_type.lower())
        except ValueError:
            pass

    # Clamp parameters
    fuzzy_threshold = max(0.0, min(1.0, fuzzy_threshold))
    limit = max(1, min(100, limit))

    results = db.search_sdn_list(
        query=query,
        sdn_type=sdn_type,
        program=program,
        fuzzy_threshold=fuzzy_threshold,
        limit=limit,
    )

    return [r.to_dict() for r in results]


@mcp.tool()
@audit_log
async def search_denied_persons(
    query: str,
    fuzzy_threshold: float = 0.7,
    limit: int = 20,
) -> list[dict]:
    """
    Search the BIS Denied Persons List.

    The Denied Persons List contains individuals and entities that have been
    denied export privileges. No person may participate in an export or
    reexport transaction subject to the EAR with a denied person.

    Denial orders are typically issued as a result of criminal convictions
    or settlements for export control violations.

    Args:
        query: Name or partial name to search for. Supports fuzzy matching.
        fuzzy_threshold: Minimum match score (0-1) for fuzzy matches.
                        Default 0.7 (70% match).
        limit: Maximum number of results to return (1-100, default 20).

    Returns:
        List of matching entries, each containing:
        - entry: Denied person details (name, addresses, denial dates, etc.)
        - match_score: Fuzzy match score (0-1)
        - match_type: How the match was found
        - matched_field: Which field matched
        - matched_value: The actual value that matched
    """
    db = get_sanctions_db()

    # Clamp parameters
    fuzzy_threshold = max(0.0, min(1.0, fuzzy_threshold))
    limit = max(1, min(100, limit))

    results = db.search_denied_persons(
        query=query,
        fuzzy_threshold=fuzzy_threshold,
        limit=limit,
    )

    return [r.to_dict() for r in results]


@mcp.tool()
@audit_log
async def check_country_sanctions(country: str) -> dict:
    """
    Get comprehensive sanctions and export control information for a country.

    Provides a summary of OFAC sanctions programs, EAR country group
    memberships, ITAR restrictions, and key export limitations applicable
    to a specific country.

    Args:
        country: Country name or ISO 3166-1 alpha-2 code. Examples:
                - "Iran" or "IR"
                - "Russia" or "RU"
                - "China" or "CN"
                - "Germany" or "DE"

    Returns:
        Dictionary containing:
        - country_code: ISO 3166-1 alpha-2 code
        - country_name: Full country name
        - ofac_programs: List of active OFAC sanctions programs
        - embargo_type: "comprehensive", "targeted", or "none"
        - ear_country_groups: EAR country group memberships (A:1, D:1, etc.)
        - itar_restricted: Whether ITAR proscribed destination (22 CFR 126.1)
        - arms_embargo: Whether subject to arms embargo
        - summary: Brief sanctions overview
        - key_restrictions: Major export limitations
        - notes: Additional considerations

        Returns error dict if country is not found.
    """
    db = get_sanctions_db()

    # Try by code first
    country_upper = country.upper().strip()
    if len(country_upper) == 2:
        # Check preloaded data
        if country_upper in COUNTRY_SANCTIONS_DATA:
            return COUNTRY_SANCTIONS_DATA[country_upper].to_dict()
        # Check database
        result = db.get_country_sanctions(country_upper)
        if result:
            return result.to_dict()

    # Try by name
    result = db.get_country_by_name(country)
    if result:
        return result.to_dict()

    # Check preloaded data by name
    for code, sanctions in COUNTRY_SANCTIONS_DATA.items():
        if country.lower() in sanctions.country_name.lower():
            return sanctions.to_dict()

    return {
        "error": f"Country '{country}' not found in sanctions database.",
        "suggestion": "Try using the full country name or ISO 3166-1 alpha-2 code.",
    }
