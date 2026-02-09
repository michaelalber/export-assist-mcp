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
    "CONTROL_REASONS",
    "COUNTRY_GROUPS",
    "ECCN_DATA",
    "GENERALLY_AUTHORIZED_DESTINATIONS",
    "GLOSSARY",
    "LICENSE_EXCEPTIONS",
    "PROHIBITED_DESTINATIONS",
    "SPECIFIC_AUTHORIZATION_ACTIVITIES",
    "USML_CATEGORIES",
    "CFR810AuthorizationType",
    "CFR810Country",
    "get_all_generally_authorized",
    "get_all_prohibited",
    "get_cfr810_authorization",
    "get_country_groups",
    "get_eccn",
    "get_glossary_term",
    "get_usml_category",
    "is_generally_authorized",
    "is_prohibited_destination",
]
