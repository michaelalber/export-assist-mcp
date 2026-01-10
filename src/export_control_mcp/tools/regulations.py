"""Regulation search tools for Export Control MCP.

Provides semantic search capabilities for EAR and ITAR regulations,
ECCN lookups, USML category information, and jurisdiction analysis.
"""

from export_control_mcp.audit import audit_log
from export_control_mcp.models.regulations import (
    ECCN,
    JurisdictionAnalysis,
    RegulationType,
    USMLCategory,
)
from export_control_mcp.resources.reference_data import (
    CONTROL_REASONS,
    LICENSE_EXCEPTIONS,
    get_country_groups,
    get_eccn,
    get_glossary_term,
    get_usml_category,
)
from export_control_mcp.server import mcp
from export_control_mcp.services import get_rag_service


@mcp.tool()
@audit_log
async def search_ear(
    query: str,
    part: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search the Export Administration Regulations (EAR) using semantic search.

    Find relevant EAR provisions based on natural language queries. Use this
    to research export control requirements, understand Commerce Department
    regulations, or find specific regulatory text.

    The EAR (15 CFR Parts 730-774) governs the export and reexport of most
    commercial items, including dual-use items that could have military
    applications.

    Args:
        query: Natural language search query describing what you're looking for.
               Examples:
               - "license requirements for encryption software"
               - "deemed export rule for foreign nationals"
               - "technology transfer restrictions"
               - "items controlled for nuclear nonproliferation"
        part: Optional filter by EAR part number. Examples:
              - "Part 730" (General Information)
              - "Part 732" (Steps for Using the EAR)
              - "Part 734" (Scope of the EAR)
              - "Part 740" (License Exceptions)
              - "Part 742" (Control Policy)
              - "Part 744" (End-User and End-Use Controls)
              - "Part 746" (Embargoes and Sanctions)
              - "Part 774" (Commerce Control List)
              Leave empty to search all parts.
        limit: Maximum number of results to return (1-50, default 10).

    Returns:
        List of matching regulation sections, each containing:
        - id: Unique chunk identifier
        - part: EAR part number (e.g., "Part 730")
        - section: Section number if available (e.g., "730.5")
        - title: Section or chunk title
        - content: Relevant text content (truncated if long)
        - citation: CFR citation (e.g., "15 CFR 730.5")
        - score: Relevance score (0-1, higher is more relevant)
    """
    rag_service = get_rag_service()

    # Clamp limit to reasonable range
    limit = max(1, min(limit, 50))

    # Perform search
    results = await rag_service.search_ear(
        query=query,
        part=part,
        limit=limit,
    )

    # Format response for MCP
    return [r.to_dict() for r in results]


@mcp.tool()
@audit_log
async def search_itar(
    query: str,
    part: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search the International Traffic in Arms Regulations (ITAR) using semantic search.

    Find relevant ITAR provisions based on natural language queries. Use this
    to research defense article controls, understand State Department regulations,
    or find specific regulatory text.

    The ITAR (22 CFR Parts 120-130) controls the export and temporary import
    of defense articles and defense services on the United States Munitions
    List (USML).

    Args:
        query: Natural language search query describing what you're looking for.
               Examples:
               - "defense article definition"
               - "brokering activities registration"
               - "temporary export exemptions"
               - "technical data controls"
        part: Optional filter by ITAR part number. Examples:
              - "Part 120" (Purpose and Definitions)
              - "Part 121" (The United States Munitions List)
              - "Part 122" (Registration and Licensing)
              - "Part 123" (Licenses for Defense Articles)
              - "Part 124" (Agreements, Off-Shore Procurement)
              - "Part 125" (Licenses for Technical Data)
              - "Part 126" (General Policies and Provisions)
              - "Part 127" (Violations and Penalties)
              - "Part 128" (Administrative Procedures)
              - "Part 129" (Registration/Licensing of Brokers)
              - "Part 130" (Political Contributions)
              Leave empty to search all parts.
        limit: Maximum number of results to return (1-50, default 10).

    Returns:
        List of matching regulation sections, each containing:
        - id: Unique chunk identifier
        - part: ITAR part number (e.g., "Part 121")
        - section: Section number if available (e.g., "121.1")
        - title: Section or chunk title
        - content: Relevant text content (truncated if long)
        - citation: CFR citation (e.g., "22 CFR 121.1")
        - score: Relevance score (0-1, higher is more relevant)
    """
    rag_service = get_rag_service()

    # Clamp limit to reasonable range
    limit = max(1, min(limit, 50))

    # Perform search
    results = await rag_service.search_itar(
        query=query,
        part=part,
        limit=limit,
    )

    # Format response for MCP
    return [r.to_dict() for r in results]


@mcp.tool()
@audit_log
async def search_regulations(
    query: str,
    regulation_type: str = "all",
    limit: int = 10,
) -> list[dict]:
    """
    Search both EAR and ITAR regulations using semantic search.

    Find relevant provisions from either regulation set based on natural
    language queries. Use this when you're unsure whether an item falls
    under Commerce (EAR) or State Department (ITAR) jurisdiction, or when
    researching broad export control topics.

    Args:
        query: Natural language search query describing what you're looking for.
               Examples:
               - "encryption export controls"
               - "defense services definition"
               - "license exception for temporary exports"
               - "foreign national access controls"
        regulation_type: Filter by regulation type. Options:
                        - "all" (default): Search both EAR and ITAR
                        - "ear": Export Administration Regulations only
                        - "itar": International Traffic in Arms Regulations only
        limit: Maximum number of results to return (1-50, default 10).

    Returns:
        List of matching regulation sections, each containing:
        - id: Unique chunk identifier
        - regulation_type: "ear" or "itar"
        - part: Part number (e.g., "Part 730" or "Part 121")
        - section: Section number if available
        - title: Section or chunk title
        - content: Relevant text content (truncated if long)
        - citation: CFR citation
        - score: Relevance score (0-1, higher is more relevant)
    """
    rag_service = get_rag_service()

    # Handle regulation type filter
    reg_type = None
    if regulation_type.lower() == "ear":
        reg_type = RegulationType.EAR
    elif regulation_type.lower() == "itar":
        reg_type = RegulationType.ITAR
    # else: None searches both

    # Clamp limit to reasonable range
    limit = max(1, min(limit, 50))

    # Perform search
    results = await rag_service.search(
        query=query,
        regulation_type=reg_type,
        limit=limit,
    )

    # Format response for MCP
    return [r.to_dict() for r in results]


@mcp.tool()
@audit_log
async def get_eccn_details(eccn: str) -> dict:
    """
    Look up details for a specific Export Control Classification Number (ECCN).

    ECCNs are alphanumeric codes that identify items on the Commerce Control List (CCL).
    Format: [Category 0-9][Product Group A-E][Control Number 001-999]
    Example: 3A001 = Category 3 (Electronics), Group A (Equipment), Number 001

    Args:
        eccn: The ECCN to look up (e.g., "3A001", "5A002", "9E003").
              Case insensitive. Optional suffix like ".a" will be preserved.

    Returns:
        Dictionary containing:
        - eccn: The normalized ECCN string
        - category: Category number (0-9)
        - category_name: Human-readable category name
        - product_group: Product group letter (A-E)
        - product_group_name: Human-readable product group name
        - control_number: Three-digit control number
        - title: ECCN title/description
        - description: Detailed description
        - control_reasons: List of control reasons (NS, MT, NP, etc.)
        - license_requirements: License requirements by country group
        - license_exceptions: Available license exceptions
        - related_eccns: Related ECCN references

        Returns error dict if ECCN format is invalid or not found.
    """
    # Try to get from reference data first
    eccn_obj = get_eccn(eccn)

    if eccn_obj is None:
        # Try to parse the ECCN format even if not in our database
        try:
            eccn_obj = ECCN.parse(eccn)
        except ValueError as e:
            return {"error": str(e)}

    return eccn_obj.to_dict()


@mcp.tool()
@audit_log
async def get_usml_category_details(category: str) -> dict:
    """
    Look up details for a United States Munitions List (USML) category.

    The USML (22 CFR 121) contains 21 categories of defense articles and
    defense services subject to ITAR export controls.

    Args:
        category: USML category number. Accepts:
                 - Roman numerals: "I", "II", "III", ... "XXI"
                 - Arabic numbers: "1", "2", "3", ... "21"
                 - Integers: 1, 2, 3, ... 21

    Returns:
        Dictionary containing:
        - category: Roman numeral designation
        - number: Arabic number (1-21)
        - title: Category title
        - description: Category description/overview
        - items: List of controlled items with designations
        - notes: Category-level notes and exemptions
        - significant_military_equipment: Whether category contains SME items

        Returns error dict if category is invalid or not found.
    """
    usml_obj = get_usml_category(category)

    if usml_obj is None:
        return {
            "error": f"USML category '{category}' not found. Valid categories are I-XXI (1-21)."
        }

    return usml_obj.to_dict()


@mcp.tool()
@audit_log
async def compare_jurisdictions(
    item_description: str,
    include_search_results: bool = True,
) -> dict:
    """
    Analyze whether an item likely falls under EAR or ITAR jurisdiction.

    This tool helps determine which export control regime applies to an item
    based on its description. It searches both EAR and ITAR regulations and
    provides indicators for each jurisdiction.

    IMPORTANT: This is a preliminary analysis tool. Final jurisdiction
    determinations require formal commodity jurisdiction requests to DDTC
    or classification requests to BIS.

    Args:
        item_description: Detailed description of the item, technology, or
                         service to analyze. Include:
                         - Technical specifications
                         - Intended use/application
                         - Industry/sector
                         - Whether designed for military use
        include_search_results: If True, includes relevant regulation excerpts
                               from both EAR and ITAR searches.

    Returns:
        Dictionary containing:
        - item_description: The analyzed item description
        - likely_jurisdiction: "EAR", "ITAR", "Dual-Use", or "Unknown"
        - confidence: "High", "Medium", or "Low"
        - ear_indicators: Factors suggesting EAR jurisdiction
        - itar_indicators: Factors suggesting ITAR jurisdiction
        - suggested_eccns: Potentially applicable ECCNs
        - suggested_usml_categories: Potentially applicable USML categories
        - reasoning: Explanation of the analysis
        - next_steps: Recommended actions for formal classification
        - ear_search_results: (if include_search_results) Relevant EAR excerpts
        - itar_search_results: (if include_search_results) Relevant ITAR excerpts
    """
    rag_service = get_rag_service()

    # Search both regulations
    ear_results = await rag_service.search_ear(query=item_description, limit=5)
    itar_results = await rag_service.search_itar(query=item_description, limit=5)

    # Analyze indicators
    ear_indicators = []
    itar_indicators = []
    suggested_eccns = []
    suggested_usml_categories = []

    # Check for military/defense keywords suggesting ITAR
    military_keywords = [
        "military", "defense", "weapon", "munition", "combat",
        "tactical", "warfighting", "ordnance", "ammunition",
        "missile", "spacecraft", "satellite", "classified",
    ]
    description_lower = item_description.lower()

    for keyword in military_keywords:
        if keyword in description_lower:
            itar_indicators.append(f"Contains military-related term: '{keyword}'")

    # Check for commercial/dual-use keywords suggesting EAR
    commercial_keywords = [
        "commercial", "civilian", "industrial", "consumer",
        "telecommunications", "computer", "software", "encryption",
    ]

    for keyword in commercial_keywords:
        if keyword in description_lower:
            ear_indicators.append(f"Contains commercial/dual-use term: '{keyword}'")

    # Analyze search results for jurisdiction hints
    if ear_results:
        ear_indicators.append(f"Found {len(ear_results)} relevant EAR provisions")
        # Extract potential ECCNs from high-scoring results
        for r in ear_results[:3]:
            if r.score > 0.5:
                ear_indicators.append(f"High relevance to {r.chunk.citation}")

    if itar_results:
        itar_indicators.append(f"Found {len(itar_results)} relevant ITAR provisions")
        for r in itar_results[:3]:
            if r.score > 0.5:
                itar_indicators.append(f"High relevance to {r.chunk.citation}")

    # Determine likely jurisdiction
    ear_score = len(ear_indicators)
    itar_score = len(itar_indicators)

    if itar_score > ear_score + 2:
        likely_jurisdiction = "ITAR"
        confidence = "Medium" if itar_score > 5 else "Low"
    elif ear_score > itar_score + 2:
        likely_jurisdiction = "EAR"
        confidence = "Medium" if ear_score > 5 else "Low"
    elif ear_score > 0 and itar_score > 0:
        likely_jurisdiction = "Dual-Use"
        confidence = "Low"
    elif ear_score > 0:
        likely_jurisdiction = "EAR"
        confidence = "Low"
    elif itar_score > 0:
        likely_jurisdiction = "ITAR"
        confidence = "Low"
    else:
        likely_jurisdiction = "Unknown"
        confidence = "Low"

    # Build reasoning
    reasoning_parts = []
    if itar_indicators:
        reasoning_parts.append(
            f"ITAR indicators ({len(itar_indicators)}): "
            + "; ".join(itar_indicators[:3])
        )
    if ear_indicators:
        reasoning_parts.append(
            f"EAR indicators ({len(ear_indicators)}): "
            + "; ".join(ear_indicators[:3])
        )

    reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Insufficient information for analysis."

    # Recommended next steps
    next_steps = [
        "Consult with your Export Control Officer for formal classification",
        "Gather complete technical specifications and intended end-use",
    ]

    if likely_jurisdiction == "ITAR" or likely_jurisdiction == "Dual-Use":
        next_steps.append("Consider submitting a Commodity Jurisdiction (CJ) request to DDTC")
    if likely_jurisdiction == "EAR" or likely_jurisdiction == "Dual-Use":
        next_steps.append("Consider requesting a formal ECCN classification from BIS")

    # Build result
    result = JurisdictionAnalysis(
        item_description=item_description,
        likely_jurisdiction=likely_jurisdiction,
        confidence=confidence,
        ear_indicators=ear_indicators,
        itar_indicators=itar_indicators,
        suggested_eccns=suggested_eccns,
        suggested_usml_categories=suggested_usml_categories,
        reasoning=reasoning,
        next_steps=next_steps,
    ).to_dict()

    # Optionally include search results
    if include_search_results:
        result["ear_search_results"] = [r.to_dict() for r in ear_results[:3]]
        result["itar_search_results"] = [r.to_dict() for r in itar_results[:3]]

    return result


@mcp.tool()
@audit_log
async def explain_export_term(term: str) -> dict:
    """
    Look up the definition of an export control term or acronym.

    Provides definitions from the EAR and ITAR regulatory glossaries,
    including context about how the term is used in export control.

    Args:
        term: The term or acronym to look up. Examples:
              - "deemed export"
              - "end-user"
              - "reexport"
              - "BIS"
              - "DDTC"
              - "fundamental research"

    Returns:
        Dictionary containing:
        - term: The looked-up term
        - definition: The term definition
        - context: Additional context about usage
        - regulation: Which regulation(s) define this term
        - related_terms: Related terms to explore
        - citations: Regulatory citations for the definition

        Returns error dict if term is not found in glossary.
    """
    result = get_glossary_term(term)

    if result is None:
        # Try case-insensitive search
        result = get_glossary_term(term.lower())

    if result is None:
        return {
            "error": f"Term '{term}' not found in export control glossary.",
            "suggestion": "Try searching regulations with search_ear or search_itar for more context.",
        }

    return result


@mcp.tool()
@audit_log
async def get_license_exception_info(exception_code: str) -> dict:
    """
    Get details about a specific EAR license exception.

    License exceptions allow exports without a license under specific
    conditions. Understanding exception requirements is critical for
    compliance.

    Args:
        exception_code: The license exception code. Examples:
                       - "LVS" (Limited Value Shipments)
                       - "TMP" (Temporary Imports/Exports)
                       - "RPL" (Servicing and Replacement Parts)
                       - "GOV" (Governments and International Organizations)
                       - "TSR" (Technology and Software Under Restriction)
                       - "ENC" (Encryption Commodities and Software)

    Returns:
        Dictionary containing:
        - code: Exception code
        - name: Full name of the exception
        - description: What the exception covers
        - ear_section: EAR section reference (Part 740.x)
        - requirements: Conditions that must be met
        - restrictions: Limitations and exclusions
        - documentation: Required documentation

        Returns error dict if exception code is not found.
    """
    code_upper = exception_code.upper().strip()

    if code_upper not in LICENSE_EXCEPTIONS:
        available = ", ".join(sorted(LICENSE_EXCEPTIONS.keys()))
        return {
            "error": f"License exception '{exception_code}' not found.",
            "available_exceptions": available,
        }

    exception_data = LICENSE_EXCEPTIONS[code_upper]
    return {
        "code": code_upper,
        **exception_data,
    }


@mcp.tool()
@audit_log
async def get_country_group_info(country: str) -> dict:
    """
    Get EAR country group memberships for a specific country.

    Country groups (defined in EAR Supplement No. 1 to Part 740) determine
    license requirements and available license exceptions. Understanding
    a country's group memberships is essential for export compliance.

    Key country groups:
    - A:1 - Wassenaar Arrangement members (favorable treatment)
    - A:5 - U.S. allies with favorable encryption treatment
    - B - Generally permissive countries
    - D:1 - National security concerns
    - D:5 - U.S. arms embargoed countries
    - E:1 - Terrorist-supporting countries (Cuba, Iran, North Korea, Syria)
    - E:2 - Unilateral embargo (Cuba)

    Args:
        country: Country name or ISO 3166-1 alpha-2 code. Examples:
                - "Germany" or "DE"
                - "China" or "CN"
                - "Japan" or "JP"
                - "Iran" or "IR"

    Returns:
        Dictionary containing:
        - country: Country name
        - country_code: ISO 3166-1 alpha-2 code
        - groups: List of country groups (e.g., ["A:1", "A:5", "B"])
        - group_details: Details about each group membership
        - license_implications: Key licensing implications
        - notes: Special considerations

        Returns error dict if country is not found.
    """
    groups = get_country_groups(country)

    if not groups:
        return {
            "error": f"Country '{country}' not found in country group database.",
            "suggestion": "Try using the full country name or ISO 3166-1 alpha-2 code.",
        }

    # Determine license implications based on groups
    implications = []
    notes = []

    if any(g.startswith("E:") for g in groups):
        implications.append("Subject to comprehensive embargo - most exports prohibited")
        notes.append("Consult OFAC sanctions requirements in addition to EAR")
    elif any(g.startswith("D:") for g in groups):
        implications.append("Enhanced license requirements for national security items")
        if "D:5" in groups:
            implications.append("U.S. arms embargo applies")

    if "A:1" in groups:
        implications.append("Favorable treatment under Wassenaar Arrangement")
    if "A:5" in groups:
        implications.append("Favorable treatment for encryption items")
    if "B" in groups:
        implications.append("Generally permissive - many license exceptions available")

    return {
        "country": country,
        "groups": groups,
        "license_implications": implications,
        "notes": notes,
    }