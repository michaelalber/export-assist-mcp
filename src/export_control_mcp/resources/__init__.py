"""Static reference data and resources."""

from export_control_mcp.resources.doe_nuclear import (
    GENERALLY_AUTHORIZED_DESTINATIONS,
    PROHIBITED_DESTINATIONS,
    SPECIFIC_AUTHORIZATION_ACTIVITIES,
    CFR810AuthorizationType,
    CFR810Country,
    get_all_generally_authorized,
    get_all_prohibited,
    get_cfr810_authorization,
    is_generally_authorized,
    is_prohibited_destination,
)
from export_control_mcp.resources.reference_data import (
    CONTROL_REASONS,
    COUNTRY_GROUPS,
    ECCN_DATA,
    GLOSSARY,
    LICENSE_EXCEPTIONS,
    USML_CATEGORIES,
    get_country_groups,
    get_eccn,
    get_glossary_term,
    get_usml_category,
)

__all__ = [
    # DOE Nuclear (10 CFR 810)
    "CFR810AuthorizationType",
    "CFR810Country",
    "GENERALLY_AUTHORIZED_DESTINATIONS",
    "PROHIBITED_DESTINATIONS",
    "SPECIFIC_AUTHORIZATION_ACTIVITIES",
    "get_all_generally_authorized",
    "get_all_prohibited",
    "get_cfr810_authorization",
    "is_generally_authorized",
    "is_prohibited_destination",
    # Reference Data
    "CONTROL_REASONS",
    "COUNTRY_GROUPS",
    "ECCN_DATA",
    "GLOSSARY",
    "LICENSE_EXCEPTIONS",
    "USML_CATEGORIES",
    "get_country_groups",
    "get_eccn",
    "get_glossary_term",
    "get_usml_category",
]
