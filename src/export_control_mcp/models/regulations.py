"""Pydantic models for export control regulations."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RegulationType(str, Enum):
    """Supported export control regulation types."""

    EAR = "ear"  # Export Administration Regulations (Commerce)
    ITAR = "itar"  # International Traffic in Arms Regulations (State)


class RegulationChunk(BaseModel):
    """A chunk of regulation text with metadata for vector storage."""

    id: str = Field(..., description="Unique chunk ID (e.g., 'ear:part-730:chunk-01')")
    regulation_type: RegulationType = Field(..., description="EAR or ITAR")
    part: str = Field(..., description="Regulation part (e.g., 'Part 730', 'Part 121')")
    section: str | None = Field(default=None, description="Section number (e.g., '730.5')")
    title: str = Field(..., description="Section or chunk title")
    content: str = Field(..., description="Full text content of this chunk")
    citation: str = Field(..., description="CFR citation (e.g., '15 CFR 730.5')")
    chunk_index: int = Field(default=0, description="Index if content was split into chunks")

    def to_embedding_text(self) -> str:
        """Generate text for embedding generation.

        Combines title and content for semantic search.
        """
        return f"{self.title}\n\n{self.content}"


class SearchResult(BaseModel):
    """Search result containing a regulation chunk with relevance score."""

    chunk: RegulationChunk = Field(..., description="The matched regulation chunk")
    score: float = Field(..., description="Relevance score (0-1, higher is better)")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "id": self.chunk.id,
            "regulation_type": self.chunk.regulation_type.value,
            "part": self.chunk.part,
            "section": self.chunk.section,
            "title": self.chunk.title,
            "content": self.chunk.content[:500] + "..."
            if len(self.chunk.content) > 500
            else self.chunk.content,
            "citation": self.chunk.citation,
            "score": round(self.score, 3),
        }


class EARPart(BaseModel):
    """Metadata about an EAR part (730-774)."""

    part_number: int = Field(..., description="Part number (730-774)")
    title: str = Field(..., description="Part title")
    description: str = Field(..., description="Brief description of the part")
    cfr_title: int = Field(default=15, description="CFR title (15 for EAR)")

    @property
    def citation(self) -> str:
        """Return the CFR citation for this part."""
        return f"{self.cfr_title} CFR Part {self.part_number}"


class ITARPart(BaseModel):
    """Metadata about an ITAR part (120-130)."""

    part_number: int = Field(..., description="Part number (120-130)")
    title: str = Field(..., description="Part title")
    description: str = Field(..., description="Brief description of the part")
    cfr_title: int = Field(default=22, description="CFR title (22 for ITAR)")

    @property
    def citation(self) -> str:
        """Return the CFR citation for this part."""
        return f"{self.cfr_title} CFR Part {self.part_number}"


# ECCN Category definitions
ECCN_CATEGORIES = {
    0: "Nuclear & Miscellaneous",
    1: "Materials, Chemicals, Microorganisms & Toxins",
    2: "Materials Processing",
    3: "Electronics",
    4: "Computers",
    5: "Telecommunications & Information Security",
    6: "Sensors & Lasers",
    7: "Navigation & Avionics",
    8: "Marine",
    9: "Aerospace & Propulsion",
}

# ECCN Product Group definitions
ECCN_PRODUCT_GROUPS = {
    "A": "Systems, Equipment, and Components",
    "B": "Test, Inspection, and Production Equipment",
    "C": "Materials",
    "D": "Software",
    "E": "Technology",
}


class ECCN(BaseModel):
    """Export Control Classification Number (ECCN) details.

    ECCNs are alphanumeric codes that identify items on the Commerce Control List.
    Format: [Category][Product Group][Control Number]
    Example: 3A001 = Category 3 (Electronics), Product Group A (Equipment), Number 001
    """

    raw: str = Field(..., description="Original ECCN string (e.g., '3A001')")
    category: int = Field(..., ge=0, le=9, description="Category number (0-9)")
    category_name: str = Field(..., description="Category name (e.g., 'Electronics')")
    product_group: str = Field(..., description="Product group letter (A-E)")
    product_group_name: str = Field(..., description="Product group name")
    control_number: str = Field(..., description="Control number (3 digits)")
    title: str = Field(default="", description="ECCN title/description")
    description: str = Field(default="", description="Detailed description")
    control_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for control (NS, MT, NP, CB, etc.)",
    )
    license_requirements: list[str] = Field(
        default_factory=list,
        description="License requirements by country group",
    )
    license_exceptions: list[str] = Field(
        default_factory=list,
        description="Available license exceptions (LVS, GBS, CIV, etc.)",
    )
    related_eccns: list[str] = Field(
        default_factory=list,
        description="Related ECCN references",
    )

    @classmethod
    def parse(cls, eccn_str: str, title: str = "", description: str = "") -> "ECCN":
        """
        Parse an ECCN string into its components.

        Args:
            eccn_str: ECCN string (e.g., "3A001", "5A002.a", "9E003")
            title: Optional title for the ECCN
            description: Optional detailed description

        Returns:
            ECCN object with parsed components

        Raises:
            ValueError: If the ECCN format is invalid
        """
        import re

        # Normalize: uppercase, remove spaces
        eccn = eccn_str.upper().strip()

        # Match pattern: digit + letter + 3 digits (+ optional suffix)
        match = re.match(r"^(\d)([A-E])(\d{3})(.*)$", eccn)
        if not match:
            raise ValueError(f"Invalid ECCN format: '{eccn_str}'. Expected format like '3A001'")

        category = int(match.group(1))
        product_group = match.group(2)
        control_number = match.group(3)

        return cls(
            raw=eccn_str.upper(),
            category=category,
            category_name=ECCN_CATEGORIES.get(category, "Unknown"),
            product_group=product_group,
            product_group_name=ECCN_PRODUCT_GROUPS.get(product_group, "Unknown"),
            control_number=control_number,
            title=title,
            description=description,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "eccn": self.raw,
            "category": self.category,
            "category_name": self.category_name,
            "product_group": self.product_group,
            "product_group_name": self.product_group_name,
            "control_number": self.control_number,
            "title": self.title,
            "description": self.description,
            "control_reasons": self.control_reasons,
            "license_requirements": self.license_requirements,
            "license_exceptions": self.license_exceptions,
            "related_eccns": self.related_eccns,
        }


# USML Category Roman numeral mapping
USML_ROMAN_TO_ARABIC = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
    "XXI": 21,
}

USML_ARABIC_TO_ROMAN = {v: k for k, v in USML_ROMAN_TO_ARABIC.items()}


class USMLItem(BaseModel):
    """An item within a USML category."""

    designation: str = Field(..., description="Item designation (e.g., '(a)', '(b)(1)')")
    description: str = Field(..., description="Item description")
    notes: list[str] = Field(default_factory=list, description="Associated notes")


class USMLCategory(BaseModel):
    """United States Munitions List (USML) Category.

    The USML (22 CFR 121) contains 21 categories of defense articles
    and services subject to ITAR controls.
    """

    number_roman: str = Field(..., description="Roman numeral (I-XXI)")
    number_arabic: int = Field(..., ge=1, le=21, description="Arabic number (1-21)")
    title: str = Field(..., description="Category title")
    description: str = Field(default="", description="Category description/overview")
    items: list[USMLItem] = Field(
        default_factory=list,
        description="Controlled items in this category",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Category-level notes and exemptions",
    )
    significant_military_equipment: bool = Field(
        default=False,
        description="Whether category contains SME items",
    )

    @classmethod
    def from_number(
        cls,
        number: int | str,
        title: str = "",
        description: str = "",
    ) -> "USMLCategory":
        """
        Create a USMLCategory from a number (Roman or Arabic).

        Args:
            number: Category number as int (1-21) or Roman numeral string
            title: Category title
            description: Category description

        Returns:
            USMLCategory object

        Raises:
            ValueError: If the number is invalid
        """
        if isinstance(number, str):
            # Try to parse as Roman numeral
            roman = number.upper().strip()
            if roman in USML_ROMAN_TO_ARABIC:
                arabic = USML_ROMAN_TO_ARABIC[roman]
            else:
                # Try parsing as Arabic number string
                try:
                    arabic = int(number)
                    roman = USML_ARABIC_TO_ROMAN.get(arabic, "")
                except ValueError as err:
                    raise ValueError(f"Invalid USML category: '{number}'") from err
        else:
            arabic = number
            roman = USML_ARABIC_TO_ROMAN.get(arabic, "")

        if not (1 <= arabic <= 21):
            raise ValueError(f"USML category must be 1-21, got: {arabic}")

        if not roman:
            raise ValueError(f"Invalid USML category number: {arabic}")

        return cls(
            number_roman=roman,
            number_arabic=arabic,
            title=title,
            description=description,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "category": self.number_roman,
            "number": self.number_arabic,
            "title": self.title,
            "description": self.description,
            "items": [
                {"designation": item.designation, "description": item.description}
                for item in self.items
            ],
            "notes": self.notes,
            "significant_military_equipment": self.significant_military_equipment,
        }


class JurisdictionAnalysis(BaseModel):
    """Result of jurisdiction analysis (EAR vs ITAR)."""

    item_description: str = Field(..., description="Description of the item analyzed")
    likely_jurisdiction: str = Field(
        ...,
        description="Most likely jurisdiction: 'EAR', 'ITAR', 'Dual-Use', or 'Unknown'",
    )
    confidence: str = Field(
        ...,
        description="Confidence level: 'High', 'Medium', or 'Low'",
    )
    ear_indicators: list[str] = Field(
        default_factory=list,
        description="Factors suggesting EAR jurisdiction",
    )
    itar_indicators: list[str] = Field(
        default_factory=list,
        description="Factors suggesting ITAR jurisdiction",
    )
    suggested_eccns: list[str] = Field(
        default_factory=list,
        description="Potentially applicable ECCNs",
    )
    suggested_usml_categories: list[str] = Field(
        default_factory=list,
        description="Potentially applicable USML categories",
    )
    reasoning: str = Field(default="", description="Explanation of the analysis")
    next_steps: list[str] = Field(
        default_factory=list,
        description="Recommended next steps for classification",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP tool response."""
        return {
            "item_description": self.item_description,
            "likely_jurisdiction": self.likely_jurisdiction,
            "confidence": self.confidence,
            "ear_indicators": self.ear_indicators,
            "itar_indicators": self.itar_indicators,
            "suggested_eccns": self.suggested_eccns,
            "suggested_usml_categories": self.suggested_usml_categories,
            "reasoning": self.reasoning,
            "next_steps": self.next_steps,
        }
