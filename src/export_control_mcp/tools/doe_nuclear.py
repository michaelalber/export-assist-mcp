"""DOE Nuclear Export Control tools for Export Control MCP.

Provides tools for 10 CFR 810 queries and DOE nuclear-related
export control guidance.
"""

from export_control_mcp.audit import audit_log
from export_control_mcp.resources.doe_nuclear import (
    CFR810AuthorizationType,
    GENERALLY_AUTHORIZED_ACTIVITIES,
    NATIONAL_LAB_GUIDANCE,
    SPECIFIC_AUTHORIZATION_ACTIVITIES,
    get_all_generally_authorized,
    get_all_prohibited,
    get_cfr810_authorization,
)
from export_control_mcp.server import mcp


@mcp.tool()
@audit_log
async def check_cfr810_country(country: str) -> dict:
    """
    Check 10 CFR 810 authorization status for a country.

    Determines whether nuclear technology assistance to a country is:
    - Generally Authorized (Appendix A) - certain activities allowed without specific DOE approval
    - Specific Authorization Required - case-by-case DOE approval needed
    - Prohibited - comprehensive sanctions prohibit nuclear assistance

    10 CFR 810 governs "Assistance to Foreign Atomic Energy Activities" and
    applies to the transfer of unclassified nuclear technology and assistance
    to foreign entities.

    Args:
        country: Country name to check (e.g., "Japan", "China", "France")
                 Common variations like "South Korea", "UK", "UAE" are supported.

    Returns:
        Dictionary containing:
        - country: Normalized country name
        - iso_code: ISO 3166-1 alpha-2 country code
        - authorization_type: One of "generally_authorized", "specific_authorization", "prohibited"
        - has_123_agreement: Whether country has a 123 Agreement with the US
        - notes: Additional context about the authorization status
        - guidance: Recommended next steps based on authorization type
    """
    result = get_cfr810_authorization(country)

    if result is None:
        return {
            "country": country,
            "error": "Country not found in database",
            "guidance": "Verify the country name and try again. "
            "Contact your export control office for assistance.",
        }

    # Build guidance based on authorization type
    if result.authorization_type == CFR810AuthorizationType.GENERALLY_AUTHORIZED:
        guidance = (
            "This country is a Generally Authorized Destination under 10 CFR 810 Appendix A. "
            "Certain nuclear technology assistance activities may proceed without specific "
            "DOE authorization, but reporting requirements may still apply. "
            "Consult 10 CFR 810.6 for generally authorized activities and "
            "coordinate with your export control office."
        )
    elif result.authorization_type == CFR810AuthorizationType.PROHIBITED:
        guidance = (
            "Nuclear technology assistance to this country is PROHIBITED. "
            "This country is subject to comprehensive U.S. sanctions. "
            "Do not proceed with any Part 810 activities. "
            "Contact your export control office immediately if you have questions."
        )
    else:  # SPECIFIC_AUTHORIZATION
        guidance = (
            "This country requires SPECIFIC AUTHORIZATION from DOE for any Part 810 activities. "
            "You must submit a request to DOE/NNSA and receive written approval before "
            "providing any nuclear technology assistance. "
            "Contact your export control office to initiate the authorization process."
        )

    return {
        "country": result.name,
        "iso_code": result.iso_code,
        "authorization_type": result.authorization_type.value,
        "has_123_agreement": result.has_123_agreement,
        "notes": result.notes,
        "guidance": guidance,
        "regulation": "10 CFR Part 810 - Assistance to Foreign Atomic Energy Activities",
    }


@mcp.tool()
@audit_log
async def list_cfr810_countries(
    authorization_type: str = "generally_authorized",
) -> dict:
    """
    List countries by their 10 CFR 810 authorization status.

    Returns a list of countries based on their Part 810 classification.
    Use this to see all Generally Authorized Destinations (Appendix A)
    or all prohibited destinations.

    Args:
        authorization_type: Type of authorization to list. Options:
            - "generally_authorized" (default): Countries in Appendix A
              where certain activities are pre-approved
            - "prohibited": Countries where nuclear assistance is prohibited
              due to comprehensive sanctions

    Returns:
        Dictionary containing:
        - authorization_type: The requested type
        - count: Number of countries in the list
        - countries: List of country names
        - description: Explanation of what this category means
        - as_of_date: Date the list was last updated
    """
    auth_type = authorization_type.lower().strip()

    if auth_type in ("generally_authorized", "appendix_a", "appendix-a"):
        countries = get_all_generally_authorized()
        return {
            "authorization_type": "generally_authorized",
            "count": len(countries),
            "countries": countries,
            "description": (
                "Generally Authorized Destinations (10 CFR 810 Appendix A). "
                "These countries have 123 Agreements with the US and meet policy criteria. "
                "Certain nuclear technology assistance activities to these countries "
                "may proceed without specific DOE authorization, though reporting "
                "requirements typically still apply."
            ),
            "as_of_date": "2025-11-24",
            "regulation": "10 CFR 810 Appendix A",
        }
    elif auth_type == "prohibited":
        countries = get_all_prohibited()
        return {
            "authorization_type": "prohibited",
            "count": len(countries),
            "countries": countries,
            "description": (
                "Prohibited destinations for nuclear technology assistance. "
                "These countries are subject to comprehensive U.S. sanctions "
                "that prohibit nuclear cooperation. No Part 810 activities "
                "are permitted to these destinations."
            ),
            "as_of_date": "2025-11-24",
            "regulation": "10 CFR 810; OFAC Comprehensive Sanctions",
        }
    else:
        return {
            "error": f"Unknown authorization_type: {authorization_type}",
            "valid_options": ["generally_authorized", "prohibited"],
        }


@mcp.tool()
@audit_log
async def get_cfr810_activities() -> dict:
    """
    Get information about 10 CFR 810 activity categories.

    Returns details about:
    - Generally Authorized Activities (810.6): Activities that may proceed
      to Appendix A countries without specific DOE approval
    - Activities Requiring Specific Authorization (810.7): Sensitive activities
      that always require case-by-case DOE approval

    This information helps determine what level of authorization is needed
    for a particular nuclear technology assistance activity.

    Returns:
        Dictionary containing:
        - generally_authorized_activities: Activities covered by 810.6
        - specific_authorization_activities: Activities requiring 810.7 approval
        - national_lab_guidance: Guidance specific to national laboratory operations
    """
    return {
        "generally_authorized_activities": {
            "description": (
                "Activities under 10 CFR 810.6 that are generally authorized "
                "for Appendix A destinations. Even when generally authorized, "
                "most activities require reporting to DOE."
            ),
            "activities": GENERALLY_AUTHORIZED_ACTIVITIES,
        },
        "specific_authorization_activities": {
            "description": (
                "Activities under 10 CFR 810.7 that ALWAYS require specific "
                "DOE authorization, regardless of destination. These include "
                "sensitive nuclear technologies."
            ),
            "activities": SPECIFIC_AUTHORIZATION_ACTIVITIES,
        },
        "national_lab_guidance": NATIONAL_LAB_GUIDANCE,
        "key_points": [
            "Sensitive nuclear technology (enrichment, reprocessing, heavy water) "
            "always requires specific authorization",
            "Even generally authorized activities typically require reporting",
            "Foreign nationals at national labs may trigger deemed export requirements",
            "Fundamental research exclusion may apply to basic nuclear science",
            "Always coordinate with your institution's export control office",
        ],
    }


@mcp.tool()
@audit_log
async def check_cfr810_activity(
    activity_description: str,
    destination_country: str,
) -> dict:
    """
    Analyze a nuclear technology activity for 10 CFR 810 requirements.

    Provides guidance on whether a described activity likely requires
    specific DOE authorization under Part 810.

    Args:
        activity_description: Description of the nuclear technology activity.
            Examples:
            - "Training foreign scientists on reactor safety procedures"
            - "Sharing uranium enrichment simulation software"
            - "Publishing research on advanced fuel cycles"
            - "Hosting a visiting researcher from Japan"
        destination_country: Country where the technology/assistance would go,
            or nationality of the recipient.

    Returns:
        Dictionary with analysis of authorization requirements including:
        - country_status: Authorization status of the destination
        - likely_requires_specific: Whether specific authorization is likely needed
        - sensitive_indicators: Any sensitive technology indicators detected
        - recommendations: Suggested next steps
    """
    # Check country status first
    country_result = get_cfr810_authorization(destination_country)

    if country_result is None:
        return {
            "error": f"Country not recognized: {destination_country}",
            "guidance": "Please verify the country name and try again.",
        }

    # Check for sensitive technology indicators
    activity_lower = activity_description.lower()
    sensitive_indicators = []

    sensitive_keywords = {
        "enrichment": "Uranium enrichment technology",
        "centrifuge": "Enrichment technology (centrifuge)",
        "gaseous diffusion": "Enrichment technology (gaseous diffusion)",
        "laser isotope": "Enrichment technology (laser)",
        "reprocessing": "Spent fuel reprocessing technology",
        "plutonium separation": "Reprocessing technology",
        "heavy water": "Heavy water production technology",
        "deuterium": "Heavy water related technology",
        "weapons": "Weapons-related (likely prohibited)",
        "classified": "Classified information (outside Part 810 scope)",
    }

    for keyword, description in sensitive_keywords.items():
        if keyword in activity_lower:
            sensitive_indicators.append(description)

    # Determine if specific authorization likely required
    likely_requires_specific = False
    reasons = []

    # Check destination
    if country_result.authorization_type == CFR810AuthorizationType.PROHIBITED:
        likely_requires_specific = True
        reasons.append("Destination country is prohibited for nuclear cooperation")
    elif country_result.authorization_type == CFR810AuthorizationType.SPECIFIC_AUTHORIZATION:
        likely_requires_specific = True
        reasons.append("Destination country is not in Appendix A")

    # Check for sensitive technology
    if sensitive_indicators:
        likely_requires_specific = True
        reasons.append("Activity involves sensitive nuclear technology")

    # Build recommendations
    if country_result.authorization_type == CFR810AuthorizationType.PROHIBITED:
        recommendations = [
            "STOP - This activity is likely prohibited",
            "Do not proceed without explicit legal guidance",
            "Contact your export control office immediately",
        ]
    elif likely_requires_specific:
        recommendations = [
            "This activity likely requires specific DOE authorization",
            "Prepare a Part 810 authorization request",
            "Contact your export control office to initiate the process",
            "Do not begin the activity until authorization is received",
        ]
    else:
        recommendations = [
            "This activity may be generally authorized under 810.6",
            "Verify that the activity falls within 810.6 categories",
            "Ensure reporting requirements are met",
            "Confirm with your export control office before proceeding",
        ]

    return {
        "activity_description": activity_description,
        "destination_country": country_result.name,
        "country_authorization_type": country_result.authorization_type.value,
        "sensitive_indicators": sensitive_indicators,
        "likely_requires_specific_authorization": likely_requires_specific,
        "reasons": reasons,
        "recommendations": recommendations,
        "disclaimer": (
            "This is preliminary guidance only. All Part 810 activities should be "
            "reviewed by your institution's export control office before proceeding."
        ),
    }
