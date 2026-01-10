"""Federal Register API service for export control updates.

Fetches recent rules, proposed rules, and notices from BIS, DDTC, and OFAC
using the official Federal Register API.

API Documentation: https://www.federalregister.gov/developers/documentation/api/v1
"""

import logging
from datetime import date, timedelta
from typing import Any

import httpx

from export_control_mcp.models.classification import FederalRegisterNotice

logger = logging.getLogger(__name__)


# Federal Register API endpoints
FR_API_BASE = "https://www.federalregister.gov/api/v1"

# Agency slugs for export control agencies
AGENCY_SLUGS = {
    "BIS": "bureau-of-industry-and-security",
    "DDTC": "state-department",  # DDTC is under State Department
    "OFAC": "treasury-department",  # OFAC is under Treasury
    "COMMERCE": "commerce-department",
    "STATE": "state-department",
    "TREASURY": "treasury-department",
}

# Keywords to filter export control related documents
EXPORT_CONTROL_KEYWORDS = [
    "export control",
    "export administration regulations",
    "EAR",
    "entity list",
    "ITAR",
    "international traffic in arms",
    "USML",
    "munitions list",
    "OFAC",
    "sanctions",
    "SDN",
    "specially designated nationals",
    "ECCN",
    "commerce control list",
    "denied persons",
    "embargo",
]


class FederalRegisterService:
    """Service for fetching export control updates from Federal Register API."""

    def __init__(self, timeout: float = 30.0):
        """
        Initialize the Federal Register service.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout
        self._base_url = FR_API_BASE

    async def search_documents(
        self,
        agency: str | None = None,
        document_type: str | None = None,
        days_back: int = 30,
        keywords: list[str] | None = None,
        per_page: int = 100,
    ) -> list[FederalRegisterNotice]:
        """
        Search Federal Register for export control documents.

        Args:
            agency: Filter by agency (BIS, DDTC, OFAC, or None for all).
            document_type: Filter by type (rule, proposed_rule, notice, or None).
            days_back: Number of days to look back (1-365).
            keywords: Additional keywords to search for.
            per_page: Number of results per page (max 1000).

        Returns:
            List of FederalRegisterNotice objects.
        """
        # Build query parameters
        params: dict[str, Any] = {
            "per_page": min(per_page, 1000),
            "order": "newest",
        }

        # Date range
        end_date = date.today()
        start_date = end_date - timedelta(days=min(days_back, 365))
        params["conditions[publication_date][gte]"] = start_date.isoformat()
        params["conditions[publication_date][lte]"] = end_date.isoformat()

        # Agency filter
        if agency:
            agency_upper = agency.upper()
            if agency_upper in AGENCY_SLUGS:
                params["conditions[agencies][]"] = AGENCY_SLUGS[agency_upper]

        # Document type filter
        if document_type:
            type_map = {
                "rule": "RULE",
                "proposed_rule": "PRORULE",
                "proposed": "PRORULE",
                "notice": "NOTICE",
            }
            if document_type.lower() in type_map:
                params["conditions[type][]"] = type_map[document_type.lower()]

        # Keyword search - combine with export control keywords
        search_terms = list(EXPORT_CONTROL_KEYWORDS)
        if keywords:
            search_terms.extend(keywords)

        # Use CFR citation filter for export control regulations
        # EAR: 15 CFR 730-774, ITAR: 22 CFR 120-130
        params["conditions[cfr][title]"] = 15  # Start with EAR

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Search for EAR-related documents
                ear_results = await self._fetch_documents(client, params)

                # Also search for ITAR (22 CFR)
                params["conditions[cfr][title]"] = 22
                itar_results = await self._fetch_documents(client, params)

                # Combine and deduplicate
                all_results = ear_results + itar_results
                seen_ids = set()
                unique_results = []
                for notice in all_results:
                    if notice.document_number not in seen_ids:
                        seen_ids.add(notice.document_number)
                        unique_results.append(notice)

                # Sort by publication date (newest first)
                unique_results.sort(
                    key=lambda x: x.publication_date,
                    reverse=True,
                )

                return unique_results

        except Exception as e:
            logger.error(f"Federal Register API error: {e}")
            return []

    async def _fetch_documents(
        self,
        client: httpx.AsyncClient,
        params: dict[str, Any],
    ) -> list[FederalRegisterNotice]:
        """Fetch documents from the API."""
        results = []

        try:
            response = await client.get(
                f"{self._base_url}/documents.json",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            for doc in data.get("results", []):
                try:
                    notice = self._parse_document(doc)
                    if notice:
                        results.append(notice)
                except Exception as e:
                    logger.warning(f"Error parsing document: {e}")
                    continue

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Federal Register API: {e}")
        except Exception as e:
            logger.error(f"Error fetching from Federal Register API: {e}")

        return results

    def _parse_document(self, doc: dict[str, Any]) -> FederalRegisterNotice | None:
        """Parse API response into FederalRegisterNotice."""
        doc_number = doc.get("document_number")
        title = doc.get("title")

        if not doc_number or not title:
            return None

        # Extract agency names
        agencies = doc.get("agencies", [])
        agency_names = [a.get("name", "") for a in agencies if a.get("name")]
        agency_str = ", ".join(agency_names) if agency_names else "Unknown"

        # Map document type
        doc_type = doc.get("type", "")
        type_map = {
            "Rule": "Rule",
            "Proposed Rule": "Proposed Rule",
            "Notice": "Notice",
            "Presidential Document": "Presidential Document",
        }
        document_type = type_map.get(doc_type, doc_type)

        # Parse dates
        pub_date = doc.get("publication_date", "")
        effective_date = doc.get("effective_on")

        # Extract affected ECCNs from abstract/body
        abstract = doc.get("abstract", "") or ""
        affected_eccns = self._extract_eccns(abstract + " " + title)

        # Extract affected countries
        affected_countries = self._extract_countries(abstract + " " + title)

        # Build Federal Register URL
        fr_url = doc.get("html_url", "")
        if not fr_url:
            fr_url = f"https://www.federalregister.gov/d/{doc_number}"

        return FederalRegisterNotice(
            document_number=doc_number,
            title=title,
            agency=agency_str,
            publication_date=pub_date,
            effective_date=effective_date,
            document_type=document_type,
            summary=abstract[:500] if abstract else "",
            docket_number=doc.get("docket_ids", [None])[0] if doc.get("docket_ids") else None,
            rin=doc.get("regulation_id_numbers", [None])[0]
            if doc.get("regulation_id_numbers")
            else None,
            affected_eccns=affected_eccns,
            affected_countries=affected_countries,
            federal_register_url=fr_url,
        )

    def _extract_eccns(self, text: str) -> list[str]:
        """Extract ECCN references from text."""
        import re

        eccns = set()

        # Pattern for ECCNs: digit + letter + 3 digits (e.g., 3A001, 5A002)
        pattern = r"\b(\d[A-E]\d{3}(?:\.[a-z])?)\b"
        matches = re.findall(pattern, text, re.IGNORECASE)

        for match in matches:
            eccns.add(match.upper())

        return sorted(eccns)

    def _extract_countries(self, text: str) -> list[str]:
        """Extract country references from text."""
        countries = set()

        # Common countries mentioned in export control context
        country_patterns = {
            "CN": ["China", "Chinese", "PRC"],
            "RU": ["Russia", "Russian", "Russian Federation"],
            "IR": ["Iran", "Iranian"],
            "KP": ["North Korea", "DPRK", "Democratic People's Republic of Korea"],
            "BY": ["Belarus", "Belarusian"],
            "SY": ["Syria", "Syrian"],
            "CU": ["Cuba", "Cuban"],
            "VE": ["Venezuela", "Venezuelan"],
        }

        text_lower = text.lower()
        for code, patterns in country_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    countries.add(code)
                    break

        return sorted(countries)

    async def get_recent_bis_updates(self, days: int = 30) -> list[FederalRegisterNotice]:
        """Get recent BIS (Bureau of Industry and Security) updates."""
        return await self.search_documents(agency="BIS", days_back=days)

    async def get_recent_ddtc_updates(self, days: int = 30) -> list[FederalRegisterNotice]:
        """Get recent DDTC (Directorate of Defense Trade Controls) updates."""
        return await self.search_documents(agency="DDTC", days_back=days)

    async def get_recent_ofac_updates(self, days: int = 30) -> list[FederalRegisterNotice]:
        """Get recent OFAC updates."""
        return await self.search_documents(agency="OFAC", days_back=days)

    async def get_all_recent_updates(self, days: int = 30) -> list[FederalRegisterNotice]:
        """Get all recent export control updates from all agencies."""
        return await self.search_documents(days_back=days)


# Singleton instance
_federal_register_service: FederalRegisterService | None = None


def get_federal_register_service() -> FederalRegisterService:
    """Get the Federal Register service singleton."""
    global _federal_register_service
    if _federal_register_service is None:
        _federal_register_service = FederalRegisterService()
    return _federal_register_service
