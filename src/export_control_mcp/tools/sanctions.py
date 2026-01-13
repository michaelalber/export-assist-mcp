"""Sanctions list search tools for Export Control MCP.

Provides search capabilities for BIS Entity List, OFAC SDN List,
Denied Persons List, and country-level sanctions information.
"""

from export_control_mcp.audit import audit_log
from export_control_mcp.models.sanctions import EntityType
from export_control_mcp.resources.country_sanctions import (
    get_country_by_name as _get_country_by_name,
)
from export_control_mcp.resources.country_sanctions import (
    get_country_sanctions as _get_country_sanctions,
)
from export_control_mcp.resources.country_sanctions import (
    get_country_sanctions_data,
)
from export_control_mcp.server import mcp
from export_control_mcp.services import get_sanctions_db


def _initialize_country_sanctions() -> None:
    """Initialize country sanctions data in the database."""
    db = get_sanctions_db()
    for sanctions in get_country_sanctions_data().values():
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
        # Check preloaded data from JSON config
        result = _get_country_sanctions(country_upper)
        if result:
            return result.to_dict()
        # Check database
        result = db.get_country_sanctions(country_upper)
        if result:
            return result.to_dict()

    # Try by name in database
    result = db.get_country_by_name(country)
    if result:
        return result.to_dict()

    # Check preloaded data by name
    result = _get_country_by_name(country)
    if result:
        return result.to_dict()

    return {
        "error": f"Country '{country}' not found in sanctions database.",
        "suggestion": "Try using the full country name or ISO 3166-1 alpha-2 code.",
    }


# CSL source list codes for filtering
CSL_SOURCE_LISTS = {
    "entity_list": "BIS Entity List",
    "denied_persons": "BIS Denied Persons List",
    "unverified_list": "BIS Unverified List",
    "meu_list": "BIS Military End User List",
    "sdn": "OFAC SDN List",
    "itar_debarred": "ITAR Debarred List",
    "nonproliferation": "Nonproliferation Sanctions",
    "ns_cmic": "NS Chinese Military-Industrial Complex",
    "capta": "CAPTA List",
    "fse": "Foreign Sanctions Evaders",
    "ssi": "Sectoral Sanctions",
}


@mcp.tool()
@audit_log
async def search_consolidated_screening_list(
    query: str,
    source_list: str | None = None,
    country: str | None = None,
    fuzzy_threshold: float = 0.7,
    limit: int = 20,
) -> list[dict]:
    """
    Search the Consolidated Screening List (CSL) for restricted parties.

    The CSL combines 13 export screening lists from Commerce, State, and Treasury:
    - BIS: Entity List, Denied Persons, Unverified List, Military End User List
    - State: ITAR Debarred, Nonproliferation Sanctions
    - Treasury: SDN, FSE, SSI, CAPTA, NS-MBS, NS-CMIC, NS-PLC

    Use this for comprehensive screening of potential transaction parties across
    all major U.S. government restricted party lists in a single search.

    Args:
        query: Name or partial name to search for. Examples:
            - "Huawei"
            - "China Telecom"
            - "Bank of Kunlun"
        source_list: Optional filter by source list code. Valid codes:
            - "entity_list" - BIS Entity List
            - "denied_persons" - BIS Denied Persons List
            - "unverified_list" - BIS Unverified List
            - "meu_list" - BIS Military End User List
            - "sdn" - OFAC SDN List
            - "itar_debarred" - ITAR Debarred List
            - "nonproliferation" - Nonproliferation Sanctions
            - "ns_cmic" - NS Chinese Military-Industrial Complex Companies
            - "capta" - CAPTA List
            Leave empty to search all lists.
        country: Optional ISO 3166-1 alpha-2 country code filter (e.g., "CN", "RU")
        fuzzy_threshold: Minimum fuzzy match score (0.0-1.0, default 0.7).
            Lower values return more results but may include false positives.
        limit: Maximum number of results to return (1-100, default 20).

    Returns:
        List of matching entries, each containing:
        - id: Unique entry identifier
        - name: Entity or individual name
        - entry_type: "entity", "individual", "vessel", or "aircraft"
        - source_list: Which screening list this entry is from
        - programs: Applicable sanctions programs
        - aliases: Alternative names
        - addresses: Known addresses
        - countries: Associated countries
        - remarks: Additional notes
        - match_score: Relevance score (0-1)
        - match_type: How the match was found ("fts_match", "fuzzy_name", "alias")
    """
    db = get_sanctions_db()

    # Clamp limit
    limit = max(1, min(limit, 100))

    # Validate source_list if provided
    if source_list and source_list not in CSL_SOURCE_LISTS:
        return [
            {
                "error": f"Invalid source_list: {source_list}",
                "valid_options": list(CSL_SOURCE_LISTS.keys()),
            }
        ]

    results = db.search_csl(
        query=query,
        source_list=source_list,
        country=country,
        fuzzy_threshold=fuzzy_threshold,
        limit=limit,
    )

    # Add source list display names
    for result in results:
        source_code = result.get("source_list", "")
        result["source_list_name"] = CSL_SOURCE_LISTS.get(source_code, source_code)

    return results


@mcp.tool()
@audit_log
async def get_csl_statistics() -> dict:
    """
    Get statistics about the Consolidated Screening List database.

    Returns counts of entries by source list, helping understand the
    coverage and composition of the screening database.

    Returns:
        Dictionary containing:
        - total_entries: Total number of CSL entries
        - by_source_list: Breakdown by source list with counts
        - last_updated: When the data was last refreshed (if available)
    """
    db = get_sanctions_db()

    stats = db.get_csl_stats()
    total = sum(stats.values())

    # Map codes to display names
    by_source = {CSL_SOURCE_LISTS.get(code, code): count for code, count in stats.items()}

    return {
        "total_entries": total,
        "by_source_list": by_source,
        "source_lists_included": list(CSL_SOURCE_LISTS.values()),
        "note": "CSL data is sourced from OpenSanctions mirror of official U.S. government lists",
    }
