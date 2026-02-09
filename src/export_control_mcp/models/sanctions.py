"""Pydantic models for sanctions list data."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SanctionsProgram(str, Enum):
    """OFAC sanctions programs."""

    SDGT = "SDGT"  # Specially Designated Global Terrorist
    SDN = "SDN"  # Specially Designated Nationals
    IRAN = "IRAN"  # Iran sanctions
    SYRIA = "SYRIA"  # Syria sanctions
    RUSSIA = "RUSSIA"  # Russia sanctions
    DPRK = "DPRK"  # North Korea sanctions
    CUBA = "CUBA"  # Cuba sanctions
    VENEZUELA = "VENEZUELA"  # Venezuela sanctions
    BELARUS = "BELARUS"  # Belarus sanctions
    CRIMEA = "CRIMEA"  # Crimea region sanctions


class EntityType(str, Enum):
    """Type of sanctioned entity."""

    INDIVIDUAL = "individual"
    ENTITY = "entity"
    VESSEL = "vessel"
    AIRCRAFT = "aircraft"


class EntityListEntry(BaseModel):
    """BIS Entity List entry.

    The Entity List (Supplement No. 4 to Part 744 of the EAR) identifies
    entities for which there is reasonable cause to believe they have been
    involved in activities contrary to U.S. national security or foreign
    policy interests.
    """

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Entity name")
    aliases: list[str] = Field(default_factory=list, description="Known aliases")
    addresses: list[str] = Field(default_factory=list, description="Known addresses")
    country: str = Field(..., description="Primary country")
    license_requirement: str = Field(
        default="",
        description="License requirement (e.g., 'For all items subject to the EAR')",
    )
    license_policy: str = Field(
        default="",
        description="License review policy (e.g., 'Presumption of denial')",
    )
    federal_register_citation: str = Field(
        default="",
        description="Federal Register citation for listing",
    )
    effective_date: date | None = Field(
        default=None,
        description="Date entity was added to list",
    )
    standard_order: str = Field(
        default="",
        description="Standard order reference if applicable",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "id": self.id,
            "name": self.name,
            "aliases": self.aliases,
            "addresses": self.addresses,
            "country": self.country,
            "license_requirement": self.license_requirement,
            "license_policy": self.license_policy,
            "federal_register_citation": self.federal_register_citation,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
        }


class SDNEntry(BaseModel):
    """OFAC Specially Designated Nationals (SDN) List entry.

    The SDN List contains individuals and entities owned or controlled by,
    or acting for or on behalf of, targeted countries. It also lists
    individuals, groups, and entities designated under programs that are
    not country-specific.
    """

    id: str = Field(..., description="Unique identifier (UID from OFAC)")
    name: str = Field(..., description="Primary name")
    sdn_type: EntityType = Field(..., description="Type of entry")
    programs: list[str] = Field(
        default_factory=list,
        description="Sanctions programs (e.g., SDGT, IRAN)",
    )
    aliases: list[str] = Field(default_factory=list, description="AKA names")
    addresses: list[str] = Field(default_factory=list, description="Known addresses")
    ids: list[dict[str, Any]] = Field(
        default_factory=list,
        description="ID documents (passport, national ID, etc.)",
    )
    nationalities: list[str] = Field(
        default_factory=list,
        description="Nationalities",
    )
    dates_of_birth: list[str] = Field(
        default_factory=list,
        description="Known dates of birth",
    )
    places_of_birth: list[str] = Field(
        default_factory=list,
        description="Known places of birth",
    )
    remarks: str = Field(default="", description="Additional remarks")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.sdn_type.value,
            "programs": self.programs,
            "aliases": self.aliases,
            "addresses": self.addresses,
            "ids": self.ids,
            "nationalities": self.nationalities,
            "dates_of_birth": self.dates_of_birth,
            "places_of_birth": self.places_of_birth,
            "remarks": self.remarks,
        }


class DeniedPersonEntry(BaseModel):
    """BIS Denied Persons List entry.

    The Denied Persons List contains individuals and entities that have been
    denied export privileges. No person may participate in an export or
    reexport transaction subject to the EAR with a denied person.
    """

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of denied person/entity")
    addresses: list[str] = Field(default_factory=list, description="Known addresses")
    effective_date: date | None = Field(
        default=None,
        description="Date denial order became effective",
    )
    expiration_date: date | None = Field(
        default=None,
        description="Date denial order expires (if applicable)",
    )
    standard_order: str = Field(
        default="",
        description="Standard order reference",
    )
    federal_register_citation: str = Field(
        default="",
        description="Federal Register citation",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "id": self.id,
            "name": self.name,
            "addresses": self.addresses,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "standard_order": self.standard_order,
            "federal_register_citation": self.federal_register_citation,
        }


class CountrySanctions(BaseModel):
    """Country-level sanctions summary.

    Aggregates information about sanctions programs, embargoes, and
    export control restrictions applicable to a specific country.
    """

    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    country_name: str = Field(..., description="Full country name")
    ofac_programs: list[str] = Field(
        default_factory=list,
        description="Active OFAC sanctions programs",
    )
    embargo_type: str = Field(
        default="none",
        description="Embargo type: 'comprehensive', 'targeted', or 'none'",
    )
    ear_country_groups: list[str] = Field(
        default_factory=list,
        description="EAR country group memberships (A:1, D:1, E:1, etc.)",
    )
    itar_restricted: bool = Field(
        default=False,
        description="Whether ITAR proscribed destination (22 CFR 126.1)",
    )
    arms_embargo: bool = Field(
        default=False,
        description="Whether subject to UN or US arms embargo",
    )
    summary: str = Field(
        default="",
        description="Brief summary of sanctions status",
    )
    key_restrictions: list[str] = Field(
        default_factory=list,
        description="Key export restrictions applicable",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Additional notes and considerations",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "ofac_programs": self.ofac_programs,
            "embargo_type": self.embargo_type,
            "ear_country_groups": self.ear_country_groups,
            "itar_restricted": self.itar_restricted,
            "arms_embargo": self.arms_embargo,
            "summary": self.summary,
            "key_restrictions": self.key_restrictions,
            "notes": self.notes,
        }


class SanctionsSearchResult(BaseModel):
    """Result from a sanctions list search with match score."""

    entry: EntityListEntry | SDNEntry | DeniedPersonEntry = Field(
        ...,
        description="The matched sanctions entry",
    )
    match_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fuzzy match score (0-1, higher is better match)",
    )
    match_type: str = Field(
        ...,
        description="Type of match: 'exact', 'fuzzy_name', 'alias', 'partial'",
    )
    matched_field: str = Field(
        default="name",
        description="Field that matched (name, alias, address, etc.)",
    )
    matched_value: str = Field(
        default="",
        description="The actual value that matched",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "entry": self.entry.to_dict(),
            "match_score": round(self.match_score, 3),
            "match_type": self.match_type,
            "matched_field": self.matched_field,
            "matched_value": self.matched_value,
        }
