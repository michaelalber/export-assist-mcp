"""Pydantic models for export classification assistance."""

from enum import Enum

from pydantic import BaseModel, Field


class ClassificationConfidence(str, Enum):
    """Confidence levels for classification suggestions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class JurisdictionType(str, Enum):
    """Types of export control jurisdiction."""

    EAR = "EAR"  # Export Administration Regulations (Commerce)
    ITAR = "ITAR"  # International Traffic in Arms Regulations (State)
    DUAL_USE = "dual_use"  # May fall under either depending on specifics
    EAR99 = "EAR99"  # Subject to EAR but not on CCL
    NOT_CONTROLLED = "not_controlled"  # Not subject to export controls


class ClassificationSuggestion(BaseModel):
    """AI-assisted classification suggestion based on item description."""

    item_description: str = Field(..., description="Description of the item being classified")
    suggested_jurisdiction: JurisdictionType = Field(
        ..., description="Suggested primary jurisdiction"
    )
    confidence: ClassificationConfidence = Field(
        ..., description="Confidence level of the suggestion"
    )
    suggested_eccns: list[str] = Field(
        default_factory=list,
        description="Suggested ECCN(s) if EAR jurisdiction",
    )
    suggested_usml_categories: list[str] = Field(
        default_factory=list,
        description="Suggested USML category/categories if ITAR jurisdiction",
    )
    reasoning: str = Field(
        default="",
        description="Explanation of why this classification is suggested",
    )
    key_factors: list[str] = Field(
        default_factory=list,
        description="Key factors that influenced the classification",
    )
    questions_to_resolve: list[str] = Field(
        default_factory=list,
        description="Questions that need to be answered for definitive classification",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Recommended next steps in the classification process",
    )
    disclaimer: str = Field(
        default="This is an AI-assisted suggestion only. Official classification requires formal commodity jurisdiction (CJ) or classification request submission to BIS or DDTC.",
        description="Legal disclaimer",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP tool response."""
        return {
            "item_description": self.item_description,
            "suggested_jurisdiction": self.suggested_jurisdiction.value,
            "confidence": self.confidence.value,
            "suggested_eccns": self.suggested_eccns,
            "suggested_usml_categories": self.suggested_usml_categories,
            "reasoning": self.reasoning,
            "key_factors": self.key_factors,
            "questions_to_resolve": self.questions_to_resolve,
            "next_steps": self.next_steps,
            "disclaimer": self.disclaimer,
        }


class DecisionTreeStep(BaseModel):
    """A single step in the classification decision tree."""

    step_number: int = Field(..., description="Step number in the sequence")
    question: str = Field(..., description="Question to answer at this step")
    guidance: str = Field(default="", description="Guidance for answering the question")
    options: list[str] = Field(
        default_factory=list,
        description="Possible answers/branches",
    )
    regulation_reference: str = Field(
        default="",
        description="Relevant CFR or regulation reference",
    )


class DecisionTreeResult(BaseModel):
    """Result of walking through the classification decision tree."""

    item_description: str = Field(..., description="Description of the item being classified")
    completed_steps: list[DecisionTreeStep] = Field(
        default_factory=list,
        description="Steps completed in the decision tree",
    )
    current_step: DecisionTreeStep | None = Field(
        default=None,
        description="Current step awaiting answer",
    )
    preliminary_result: str = Field(
        default="",
        description="Preliminary classification result based on answers so far",
    )
    is_complete: bool = Field(
        default=False,
        description="Whether the decision tree has reached a conclusion",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP tool response."""
        return {
            "item_description": self.item_description,
            "completed_steps": [
                {
                    "step_number": step.step_number,
                    "question": step.question,
                    "guidance": step.guidance,
                    "options": step.options,
                    "regulation_reference": step.regulation_reference,
                }
                for step in self.completed_steps
            ],
            "current_step": {
                "step_number": self.current_step.step_number,
                "question": self.current_step.question,
                "guidance": self.current_step.guidance,
                "options": self.current_step.options,
                "regulation_reference": self.current_step.regulation_reference,
            }
            if self.current_step
            else None,
            "preliminary_result": self.preliminary_result,
            "is_complete": self.is_complete,
        }


class LicenseExceptionEligibility(str, Enum):
    """Eligibility status for a license exception."""

    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    MAYBE_ELIGIBLE = "maybe_eligible"  # Requires further review
    NOT_APPLICABLE = "not_applicable"  # Exception doesn't apply to this ECCN


class LicenseExceptionCheck(BaseModel):
    """Result of checking a specific license exception's applicability."""

    exception_code: str = Field(..., description="License exception code (e.g., 'LVS', 'TMP')")
    exception_name: str = Field(..., description="Full name of the license exception")
    eligibility: LicenseExceptionEligibility = Field(..., description="Eligibility determination")
    reason: str = Field(default="", description="Explanation of the eligibility determination")
    conditions: list[str] = Field(
        default_factory=list,
        description="Conditions that must be met to use this exception",
    )
    restrictions: list[str] = Field(
        default_factory=list,
        description="Restrictions on using this exception",
    )


class LicenseExceptionEvaluation(BaseModel):
    """Comprehensive evaluation of license exception applicability for a transaction."""

    eccn: str = Field(..., description="ECCN of the item being exported")
    destination_country: str = Field(..., description="Destination country code or name")
    end_use: str = Field(default="", description="Intended end-use of the item")
    end_user_type: str = Field(
        default="", description="Type of end-user (commercial, government, etc.)"
    )
    exceptions_checked: list[LicenseExceptionCheck] = Field(
        default_factory=list,
        description="Results of checking each potentially applicable license exception",
    )
    recommended_exception: str | None = Field(
        default=None,
        description="Recommended license exception if any are available",
    )
    requires_license: bool = Field(
        default=True,
        description="Whether a license is required (no exceptions apply)",
    )
    summary: str = Field(default="", description="Summary of the evaluation")
    warnings: list[str] = Field(
        default_factory=list,
        description="Important warnings or considerations",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP tool response."""
        return {
            "eccn": self.eccn,
            "destination_country": self.destination_country,
            "end_use": self.end_use,
            "end_user_type": self.end_user_type,
            "exceptions_checked": [
                {
                    "exception_code": check.exception_code,
                    "exception_name": check.exception_name,
                    "eligibility": check.eligibility.value,
                    "reason": check.reason,
                    "conditions": check.conditions,
                    "restrictions": check.restrictions,
                }
                for check in self.exceptions_checked
            ],
            "recommended_exception": self.recommended_exception,
            "requires_license": self.requires_license,
            "summary": self.summary,
            "warnings": self.warnings,
        }


class FederalRegisterNotice(BaseModel):
    """A Federal Register notice related to export controls."""

    document_number: str = Field(..., description="Federal Register document number")
    title: str = Field(..., description="Notice title")
    agency: str = Field(..., description="Issuing agency (BIS, DDTC, OFAC, etc.)")
    publication_date: str = Field(..., description="Publication date (YYYY-MM-DD)")
    effective_date: str | None = Field(
        default=None, description="Effective date if different from publication"
    )
    document_type: str = Field(
        default="Rule", description="Type of document (Rule, Proposed Rule, Notice, etc.)"
    )
    summary: str = Field(default="", description="Summary of the notice")
    docket_number: str | None = Field(default=None, description="Docket number if applicable")
    rin: str | None = Field(default=None, description="Regulation Identifier Number")
    affected_eccns: list[str] = Field(
        default_factory=list, description="ECCNs affected by this notice"
    )
    affected_countries: list[str] = Field(
        default_factory=list, description="Countries affected by this notice"
    )
    federal_register_url: str = Field(
        default="", description="URL to the Federal Register document"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP tool response."""
        return {
            "document_number": self.document_number,
            "title": self.title,
            "agency": self.agency,
            "publication_date": self.publication_date,
            "effective_date": self.effective_date,
            "document_type": self.document_type,
            "summary": self.summary,
            "docket_number": self.docket_number,
            "rin": self.rin,
            "affected_eccns": self.affected_eccns,
            "affected_countries": self.affected_countries,
            "federal_register_url": self.federal_register_url,
        }
