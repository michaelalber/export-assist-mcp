"""Classification assistance tools for Export Control MCP.

Provides tools for AI-assisted classification suggestions, decision tree
guidance, and license exception evaluation.
"""

from typing import Any

from export_control_mcp.audit import audit_log
from export_control_mcp.models.classification import (
    ClassificationConfidence,
    ClassificationSuggestion,
    DecisionTreeResult,
    DecisionTreeStep,
    JurisdictionType,
    LicenseExceptionCheck,
    LicenseExceptionEligibility,
    LicenseExceptionEvaluation,
)
from export_control_mcp.resources.reference_data import (
    ECCN_DATA,
    LICENSE_EXCEPTIONS,
    USML_CATEGORIES,
    get_eccn,
)
from export_control_mcp.server import mcp

# Keywords that suggest ITAR jurisdiction
ITAR_KEYWORDS = [
    "military",
    "defense",
    "weapon",
    "munition",
    "ordnance",
    "missile",
    "rocket",
    "torpedo",
    "bomb",
    "grenade",
    "warship",
    "tank",
    "armored",
    "combat",
    "soldier",
    "troop",
    "army",
    "navy",
    "air force",
    "marine",
    "classified",
    "secret",
    "top secret",
    "confidential",
    "spacecraft",
    "satellite",
    "directed energy",
    "laser weapon",
    "nuclear weapon",
    "biological agent",
    "chemical agent",
    "toxin",
    "firearms",
    "ammunition",
    "silencer",
    "suppressor",
    "night vision",
    "thermal imaging",
    "infrared",
    "cryptographic",
    "stealth",
    "radar",
    "sonar",
    "torpedo",
    "submarine",
    "unmanned aerial vehicle",
    "uav",
    "drone",
    "surveillance",
    "reconnaissance",
]

# Keywords that suggest EAR jurisdiction (dual-use)
EAR_KEYWORDS = [
    "commercial",
    "industrial",
    "semiconductor",
    "integrated circuit",
    "computer",
    "software",
    "telecommunications",
    "network",
    "encryption",
    "laser",
    "sensor",
    "navigation",
    "gps",
    "inertial",
    "accelerometer",
    "gyroscope",
    "thermal",
    "camera",
    "imaging",
    "spectrometer",
    "mass spectrometer",
    "centrifuge",
    "vacuum",
    "composite",
    "carbon fiber",
    "titanium",
    "maraging steel",
    "machine tool",
    "cnc",
    "3d printer",
    "additive manufacturing",
    "chemical",
    "precursor",
    "biological",
    "pathogen",
    "toxin",
    "nuclear",
    "reactor",
    "enrichment",
    "gas turbine",
    "rocket engine",
]

# ECCN category keywords for suggesting classifications
ECCN_CATEGORY_KEYWORDS = {
    0: ["nuclear", "reactor", "enrichment", "uranium", "plutonium", "deuterium", "tritium"],
    1: ["chemical", "precursor", "biological", "pathogen", "toxin", "composite", "alloy", "fiber"],
    2: ["machine tool", "cnc", "manufacturing", "processing", "casting", "forging", "welding"],
    3: [
        "electronic",
        "semiconductor",
        "integrated circuit",
        "microprocessor",
        "fpga",
        "asic",
        "rf",
    ],
    4: ["computer", "digital", "processor", "storage", "memory", "server", "supercomputer"],
    5: [
        "telecommunications",
        "encryption",
        "cryptography",
        "network",
        "wireless",
        "satellite comm",
    ],
    6: ["sensor", "laser", "camera", "imaging", "optical", "infrared", "thermal", "spectrometer"],
    7: ["navigation", "inertial", "gps", "gyroscope", "accelerometer", "altimeter", "avionics"],
    8: ["marine", "submarine", "underwater", "sonar", "propeller", "hull"],
    9: ["aerospace", "propulsion", "turbine", "rocket", "engine", "spacecraft", "uav"],
}


def _analyze_description(description: str) -> dict[str, Any]:
    """Analyze item description for classification indicators."""
    desc_lower = description.lower()

    itar_matches = [kw for kw in ITAR_KEYWORDS if kw in desc_lower]
    ear_matches = [kw for kw in EAR_KEYWORDS if kw in desc_lower]

    # Check ECCN category keywords
    category_matches = {}
    for cat, keywords in ECCN_CATEGORY_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in desc_lower]
        if matches:
            category_matches[cat] = matches

    return {
        "itar_keywords": itar_matches,
        "ear_keywords": ear_matches,
        "category_matches": category_matches,
    }


@mcp.tool()
@audit_log
async def suggest_classification(
    item_description: str,
    additional_context: str = "",
) -> dict[str, Any]:
    """
    Provide AI-assisted classification suggestion for an item.

    Analyzes the item description to suggest likely export control
    jurisdiction (EAR or ITAR) and potential classification numbers
    (ECCN or USML category).

    IMPORTANT: This is an advisory tool only. Official classification
    requires formal commodity jurisdiction (CJ) determination from DDTC
    or classification request to BIS.

    Args:
        item_description: Detailed description of the item to be classified.
                         Include technical specifications, intended use,
                         and any military or defense-related applications.
                         Examples:
                         - "Thermal imaging camera with 640x480 resolution, NETD < 50mK"
                         - "CNC milling machine with 5-axis capability"
                         - "Military-grade body armor rated NIJ Level IV"
        additional_context: Optional context about the item's design origin,
                          end-use, or customer. This helps refine the
                          classification suggestion.

    Returns:
        Dictionary containing:
        - suggested_jurisdiction: "EAR", "ITAR", "dual_use", or "EAR99"
        - confidence: "high", "medium", or "low"
        - suggested_eccns: List of potentially applicable ECCNs
        - suggested_usml_categories: List of potentially applicable USML categories
        - reasoning: Explanation of the classification suggestion
        - key_factors: Factors that influenced the suggestion
        - questions_to_resolve: Questions that need answers for definitive classification
        - next_steps: Recommended next steps
        - disclaimer: Legal disclaimer about the advisory nature
    """
    analysis = _analyze_description(item_description + " " + additional_context)

    itar_score = len(analysis["itar_keywords"])
    ear_score = len(analysis["ear_keywords"])

    # Determine likely jurisdiction
    if itar_score > ear_score * 2:
        jurisdiction = JurisdictionType.ITAR
        confidence = (
            ClassificationConfidence.MEDIUM if itar_score >= 3 else ClassificationConfidence.LOW
        )
    elif ear_score > itar_score * 2:
        jurisdiction = JurisdictionType.EAR
        confidence = (
            ClassificationConfidence.MEDIUM if ear_score >= 3 else ClassificationConfidence.LOW
        )
    elif itar_score > 0 and ear_score > 0:
        jurisdiction = JurisdictionType.DUAL_USE
        confidence = ClassificationConfidence.LOW
    elif ear_score > 0:
        jurisdiction = JurisdictionType.EAR
        confidence = ClassificationConfidence.LOW
    else:
        jurisdiction = JurisdictionType.EAR99
        confidence = ClassificationConfidence.LOW

    # Suggest ECCNs based on category matches
    suggested_eccns = []
    if analysis["category_matches"]:
        for category in sorted(analysis["category_matches"].keys()):
            # Look for ECCNs in this category from our reference data
            for eccn in ECCN_DATA:
                if eccn.startswith(str(category)):
                    suggested_eccns.append(eccn)
                    if len(suggested_eccns) >= 5:
                        break
            if len(suggested_eccns) >= 5:
                break

    # Suggest USML categories for ITAR items
    suggested_usml = []
    if jurisdiction in [JurisdictionType.ITAR, JurisdictionType.DUAL_USE]:
        desc_lower = item_description.lower()
        for cat_num, cat_data in USML_CATEGORIES.items():
            title_lower = cat_data["title"].lower()
            desc_cat = cat_data["description"].lower()
            if any(word in title_lower or word in desc_cat for word in desc_lower.split()):
                suggested_usml.append(f"Category {cat_num} - {cat_data['title']}")
                if len(suggested_usml) >= 3:
                    break

    # Build key factors
    key_factors = []
    if analysis["itar_keywords"]:
        key_factors.append(
            f"ITAR-related terms detected: {', '.join(analysis['itar_keywords'][:5])}"
        )
    if analysis["ear_keywords"]:
        key_factors.append(
            f"Dual-use/EAR terms detected: {', '.join(analysis['ear_keywords'][:5])}"
        )
    if analysis["category_matches"]:
        cats = [f"Category {c}" for c in analysis["category_matches"]]
        key_factors.append(f"Potentially relevant ECCN categories: {', '.join(cats)}")

    # Build reasoning
    reasoning_parts = []
    if jurisdiction == JurisdictionType.ITAR:
        reasoning_parts.append(
            "Item appears to be primarily designed for military/defense applications."
        )
    elif jurisdiction == JurisdictionType.DUAL_USE:
        reasoning_parts.append("Item has both commercial and potential military applications.")
    elif jurisdiction == JurisdictionType.EAR:
        reasoning_parts.append(
            "Item appears to be a dual-use commercial item potentially controlled under EAR."
        )
    else:
        reasoning_parts.append("Item does not appear to match specific control list entries.")

    reasoning = " ".join(reasoning_parts)

    # Questions to resolve
    questions = [
        "Was this item specifically designed, developed, or modified for military use?",
        "Is the item derived from or related to classified technology?",
        "What are the exact technical specifications (parameters that may trigger control thresholds)?",
        "Who is the intended end-user and what is the intended end-use?",
    ]

    # Next steps
    next_steps = [
        "Review the suggested ECCN/USML entries in detail",
        "Compare item specifications against control list technical parameters",
        "Consult with export control officer or legal counsel",
    ]
    if jurisdiction == JurisdictionType.ITAR or jurisdiction == JurisdictionType.DUAL_USE:
        next_steps.append("Consider submitting Commodity Jurisdiction (CJ) request to DDTC")
    if jurisdiction in [JurisdictionType.EAR, JurisdictionType.DUAL_USE, JurisdictionType.EAR99]:
        next_steps.append("Consider submitting classification request to BIS")

    suggestion = ClassificationSuggestion(
        item_description=item_description,
        suggested_jurisdiction=jurisdiction,
        confidence=confidence,
        suggested_eccns=suggested_eccns,
        suggested_usml_categories=suggested_usml,
        reasoning=reasoning,
        key_factors=key_factors,
        questions_to_resolve=questions,
        next_steps=next_steps,
    )

    return suggestion.to_dict()


@mcp.tool()
@audit_log
async def classification_decision_tree(
    item_description: str,
    step: int = 1,
) -> dict[str, Any]:
    """
    Walk through the classification decision tree step by step.

    Provides structured guidance through the export control classification
    process, helping users determine the appropriate classification for
    their item.

    This tool implements a simplified version of the BIS classification
    decision tree and can be called iteratively to walk through each step.

    Args:
        item_description: Description of the item being classified.
        step: Current step number in the decision tree (1-based).
              Call with step=1 to start, then increment based on answers.

    Returns:
        Dictionary containing:
        - item_description: The item being classified
        - completed_steps: Steps already completed
        - current_step: Current step with question, guidance, and options
        - preliminary_result: Preliminary classification if determined
        - is_complete: Whether classification is complete
    """
    # Decision tree steps
    decision_steps = [
        DecisionTreeStep(
            step_number=1,
            question="Is the item subject to the exclusive jurisdiction of another U.S. government agency?",
            guidance="Items controlled by other agencies (e.g., NRC for nuclear materials, DOE for atomic energy) are not subject to the EAR. ITAR items are controlled by DDTC (State Department).",
            options=[
                "Yes - Subject to ITAR (defense article)",
                "Yes - Subject to other agency (NRC, DOE, etc.)",
                "No - Potentially subject to EAR",
                "Unsure - Need commodity jurisdiction determination",
            ],
            regulation_reference="15 CFR 734.3",
        ),
        DecisionTreeStep(
            step_number=2,
            question="Is the item 'publicly available' technology or software, or the result of fundamental research?",
            guidance="'Publicly available' means published or generally accessible. 'Fundamental research' is basic/applied research ordinarily published and shared broadly.",
            options=[
                "Yes - Published or publicly available",
                "Yes - Result of fundamental research at accredited institution",
                "No - Proprietary, controlled, or restricted information",
                "Partially - Some aspects may be publicly available",
            ],
            regulation_reference="15 CFR 734.7-734.8",
        ),
        DecisionTreeStep(
            step_number=3,
            question="Is the item listed on the Commerce Control List (CCL)?",
            guidance="Review the CCL (15 CFR 774 Supplement 1) to determine if the item matches a specific ECCN entry. Check technical parameters against control thresholds.",
            options=[
                "Yes - Item matches a specific ECCN",
                "No - Item does not match any ECCN (may be EAR99)",
                "Partially - Meets some but not all parameters",
                "Unsure - Need detailed technical review",
            ],
            regulation_reference="15 CFR 774",
        ),
        DecisionTreeStep(
            step_number=4,
            question="What is the reason for control for the applicable ECCN?",
            guidance="ECCNs have specific reasons for control (NS, MT, NP, CB, CC, etc.) which determine license requirements. Check the 'Reason for Control' column.",
            options=[
                "NS - National Security",
                "MT - Missile Technology",
                "NP - Nuclear Nonproliferation",
                "CB - Chemical & Biological Weapons",
                "CC - Crime Control",
                "AT - Anti-Terrorism (most ECCNs have this)",
                "Multiple reasons for control",
            ],
            regulation_reference="15 CFR 742",
        ),
        DecisionTreeStep(
            step_number=5,
            question="Does a license exception apply to this transaction?",
            guidance="Review available license exceptions in 15 CFR 740. Consider destination country, end-user, and end-use restrictions.",
            options=[
                "Yes - License exception available (specify which)",
                "No - No license exception applies",
                "Maybe - Need to verify exception conditions",
            ],
            regulation_reference="15 CFR 740",
        ),
    ]

    # Clamp step to valid range
    step = max(1, min(step, len(decision_steps)))

    current = decision_steps[step - 1]
    completed = decision_steps[: step - 1]

    # Determine if we've reached a conclusion
    is_complete = step > len(decision_steps)
    preliminary_result = ""

    if step == len(decision_steps):
        preliminary_result = "Based on your answers, proceed to determine if a license is required using the Commerce Country Chart (15 CFR 738 Supplement 1) for your specific destination."

    result = DecisionTreeResult(
        item_description=item_description,
        completed_steps=completed,
        current_step=current if not is_complete else None,
        preliminary_result=preliminary_result,
        is_complete=is_complete,
    )

    return result.to_dict()


@mcp.tool()
@audit_log
async def check_license_exception(
    eccn: str,
    destination_country: str,
    end_use: str = "",
    end_user_type: str = "commercial",
) -> dict[str, Any]:
    """
    Evaluate which license exceptions may apply to a specific export transaction.

    Analyzes the ECCN, destination, and end-use to determine which EAR
    license exceptions might be available. This is an advisory evaluation
    only - always verify conditions with the actual regulations.

    Args:
        eccn: Export Control Classification Number (e.g., "3A001", "5A002").
             Use "EAR99" for items not on the CCL.
        destination_country: Destination country code (e.g., "DE", "CN") or name.
        end_use: Description of the intended end-use of the item.
        end_user_type: Type of end-user. Options:
                      - "commercial" (default)
                      - "government"
                      - "military"
                      - "individual"

    Returns:
        Dictionary containing:
        - eccn: The ECCN checked
        - destination_country: The destination
        - exceptions_checked: List of license exceptions evaluated
        - recommended_exception: Recommended exception if available
        - requires_license: Whether a license is still required
        - summary: Summary of the evaluation
        - warnings: Important warnings or caveats
    """
    # Parse ECCN to get available exceptions
    eccn_info = get_eccn(eccn.upper())
    available_exceptions = []

    if eccn_info:
        available_exceptions = eccn_info.license_exceptions
    elif eccn.upper() == "EAR99":
        # EAR99 items generally don't require a license to most destinations
        available_exceptions = ["NLR"]

    # Check if destination is in restricted country groups
    dest_upper = destination_country.upper().strip()
    is_embargoed = False
    is_restricted = False

    # Check country groups
    if dest_upper in ["CU", "IR", "KP", "SY"]:  # E:1 countries
        is_embargoed = True
    elif dest_upper in ["RU", "BY", "CN", "VE"]:  # Heavily restricted
        is_restricted = True

    # Evaluate each potentially applicable exception
    exceptions_checked = []

    for exc_code in LICENSE_EXCEPTIONS:
        exc_info = LICENSE_EXCEPTIONS[exc_code]

        eligibility = LicenseExceptionEligibility.NOT_APPLICABLE
        reason = ""
        conditions = []
        restrictions = []

        if exc_code in available_exceptions:
            if is_embargoed:
                eligibility = LicenseExceptionEligibility.NOT_ELIGIBLE
                reason = "License exceptions generally not available to embargoed countries"
                restrictions = [f"Country {dest_upper} is subject to comprehensive embargo"]
            elif is_restricted and exc_code in ["LVS", "GBS", "CIV"]:
                eligibility = LicenseExceptionEligibility.NOT_ELIGIBLE
                reason = f"Exception {exc_code} not available to this destination"
                restrictions = [f"Country {dest_upper} is excluded from this exception"]
            elif exc_code == "TMP":
                eligibility = LicenseExceptionEligibility.MAYBE_ELIGIBLE
                reason = "TMP may be available for temporary exports"
                conditions = [
                    "Item must be returned within specified timeframe",
                    "Must maintain effective control of the item",
                    "Proper documentation required",
                ]
            elif exc_code == "TSU":
                eligibility = LicenseExceptionEligibility.MAYBE_ELIGIBLE
                reason = "TSU may be available for publicly available technology"
                conditions = [
                    "Technology must be publicly available",
                    "Not for military end-use in restricted countries",
                ]
            elif exc_code == "GOV":
                if end_user_type == "government":
                    eligibility = LicenseExceptionEligibility.MAYBE_ELIGIBLE
                    reason = "GOV may be available for U.S. government activities"
                    conditions = [
                        "Must be for official U.S. government use",
                        "Proper authorization from contracting agency required",
                    ]
                else:
                    eligibility = LicenseExceptionEligibility.NOT_ELIGIBLE
                    reason = "GOV only available for U.S. government end-users"
            elif exc_code == "LVS":
                eligibility = LicenseExceptionEligibility.MAYBE_ELIGIBLE
                reason = "LVS may be available for shipments under value threshold"
                conditions = [
                    "Total value must be under $1,500 (check specific limits)",
                    "Destination must be in approved country group",
                    "Not for certain sensitive ECCNs",
                ]
            elif exc_code == "GBS":
                eligibility = LicenseExceptionEligibility.MAYBE_ELIGIBLE
                reason = "GBS may be available for Group B countries"
                conditions = [
                    "Destination must be in Country Group B",
                    "End-user screening required",
                ]
            else:
                eligibility = LicenseExceptionEligibility.MAYBE_ELIGIBLE
                reason = f"Exception {exc_code} potentially applicable - verify conditions"
                conditions = [f"Review requirements in {exc_info['cfr']}"]
        else:
            reason = f"Exception {exc_code} not listed as available for ECCN {eccn}"

        exceptions_checked.append(
            LicenseExceptionCheck(
                exception_code=exc_code,
                exception_name=exc_info["name"],
                eligibility=eligibility,
                reason=reason,
                conditions=conditions,
                restrictions=restrictions,
            )
        )

    # Determine recommendation
    eligible_exceptions = [
        e
        for e in exceptions_checked
        if e.eligibility
        in [LicenseExceptionEligibility.ELIGIBLE, LicenseExceptionEligibility.MAYBE_ELIGIBLE]
    ]

    recommended = None
    requires_license = True

    if eligible_exceptions:
        recommended = eligible_exceptions[0].exception_code
        requires_license = False  # At least one exception may apply

    # Build summary
    if is_embargoed:
        summary = f"Export to {destination_country} requires a license. This destination is subject to comprehensive embargo, and license exceptions are generally not available."
    elif requires_license:
        summary = f"No license exception appears to be available for ECCN {eccn} to {destination_country}. A license application to BIS may be required."
    else:
        summary = f"License exception {recommended} may be available. Verify all conditions are met before proceeding."

    # Warnings
    warnings = [
        "This evaluation is advisory only - verify all conditions in the actual regulations",
        "End-user and end-use restrictions apply regardless of license exceptions",
        "Screen all parties against denied persons and entity lists",
    ]
    if end_user_type == "military":
        warnings.append("Military end-use may trigger additional restrictions under 15 CFR 744.21")

    evaluation = LicenseExceptionEvaluation(
        eccn=eccn,
        destination_country=destination_country,
        end_use=end_use,
        end_user_type=end_user_type,
        exceptions_checked=exceptions_checked,
        recommended_exception=recommended,
        requires_license=requires_license if is_embargoed else not bool(eligible_exceptions),
        summary=summary,
        warnings=warnings,
    )

    return evaluation.to_dict()


@mcp.tool()
@audit_log
async def get_recent_updates(
    agency: str = "all",
    days: int = 30,
    document_type: str = "all",
) -> list[dict[str, Any]]:
    """
    Get recent export control regulatory updates from the Federal Register.

    Fetches real-time data from the official Federal Register API
    (https://www.federalregister.gov/developers/documentation/api/v1).

    Returns summaries of recent rules, proposed rules, and notices from
    BIS, DDTC, and OFAC that may affect export control classifications
    and licensing requirements.

    Args:
        agency: Filter by agency. Options:
               - "all" (default) - All agencies
               - "BIS" - Bureau of Industry and Security
               - "DDTC" - Directorate of Defense Trade Controls
               - "OFAC" - Office of Foreign Assets Control
        days: Number of days to look back (1-365, default 30).
        document_type: Filter by document type. Options:
                      - "all" (default) - All types
                      - "rule" - Final rules
                      - "proposed" - Proposed rules
                      - "notice" - Notices

    Returns:
        List of Federal Register notices, each containing:
        - document_number: FR document number
        - title: Notice title
        - agency: Issuing agency
        - publication_date: Date published
        - effective_date: When changes take effect
        - document_type: Type of document
        - summary: Brief summary
        - affected_eccns: ECCNs affected (if applicable)
        - affected_countries: Countries affected (if applicable)
        - federal_register_url: Link to full document
    """
    from export_control_mcp.services.federal_register import get_federal_register_service

    # Clamp days to valid range
    days = max(1, min(365, days))

    # Get the Federal Register service
    fr_service = get_federal_register_service()

    # Determine agency filter
    agency_filter = None if agency.lower() == "all" else agency.upper()

    # Determine document type filter
    doc_type_filter = None if document_type.lower() == "all" else document_type.lower()

    # Fetch from Federal Register API
    try:
        notices = await fr_service.search_documents(
            agency=agency_filter,
            document_type=doc_type_filter,
            days_back=days,
        )

        return [notice.to_dict() for notice in notices]

    except Exception as e:
        # Log error and return empty list
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching from Federal Register API: {e}")
        return []
