"""Consolidated Screening List (CSL) ingestion.

Downloads and parses the CSL which combines 13 screening lists from:
- Department of Commerce (Entity List, Denied Persons, Unverified List, MEU List)
- Department of State (AECA Debarred, Nonproliferation Sanctions)
- Department of Treasury (SDN, FSE, SSI, CAPTA, NS-MBS, NS-CMIC, NS-PLC)

Primary source: OpenSanctions mirror (more reliable than official endpoints)
Fallback: Official trade.gov endpoints

Sources:
- https://www.trade.gov/consolidated-screening-list
- https://www.opensanctions.org/datasets/us_trade_csl/
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from export_control_mcp.models.sanctions import EntityType
from export_control_mcp.services.sanctions_db import SanctionsDBService

logger = logging.getLogger(__name__)


# CSL data sources
CSL_SOURCES = {
    # Primary: OpenSanctions mirror (more reliable)
    "opensanctions": "https://data.opensanctions.org/datasets/latest/us_trade_csl/source.json",
    # Official sources (may have availability issues)
    "trade_gov_json": "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.json",
    "trade_gov_csv": "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv",
}

# Map CSL sources to our list types
CSL_SOURCE_MAPPING = {
    # Commerce Department
    "Denied Persons List (DPL) - Bureau of Industry and Security": "denied_persons",
    "Entity List (EL) - Bureau of Industry and Security": "entity_list",
    "Unverified List (UVL) - Bureau of Industry and Security": "unverified_list",
    "Military End User (MEU) List - Bureau of Industry and Security": "meu_list",
    # State Department
    "ITAR Debarred (DTC) - State Department": "itar_debarred",
    "Nonproliferation Sanctions (ISN) - State Department": "nonproliferation",
    # Treasury Department
    "Specially Designated Nationals (SDN) - Treasury Department": "sdn",
    "Foreign Sanctions Evaders (FSE) - Treasury Department": "fse",
    "Sectoral Sanctions Identifications List (SSI) - Treasury Department": "ssi",
    "Capta List (CAP) - Treasury Department": "capta",
    "Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department": "ns_mbs",
    "Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department": "ns_cmic",
    "Palestinian Legislative Council List (NS-PLC List) - Treasury Department": "ns_plc",
}

# Simplified source name mapping
CSL_SOURCE_NAMES = {
    "denied_persons": "BIS Denied Persons List",
    "entity_list": "BIS Entity List",
    "unverified_list": "BIS Unverified List",
    "meu_list": "BIS Military End User List",
    "itar_debarred": "ITAR Debarred List",
    "nonproliferation": "Nonproliferation Sanctions",
    "sdn": "OFAC SDN List",
    "fse": "Foreign Sanctions Evaders",
    "ssi": "Sectoral Sanctions",
    "capta": "CAPTA List",
    "ns_mbs": "NS Menu-Based Sanctions",
    "ns_cmic": "NS Chinese Military-Industrial Complex",
    "ns_plc": "Palestinian Legislative Council",
}


@dataclass
class CSLEntry:
    """A single entry from the Consolidated Screening List."""

    id: str
    name: str
    entry_type: EntityType
    source_list: str
    source_list_code: str
    programs: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    addresses: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    ids: list[dict[str, str]] = field(default_factory=list)
    remarks: str = ""
    source_url: str = ""
    federal_register_citation: str = ""

    def to_search_text(self) -> str:
        """Generate searchable text for this entry."""
        parts = [
            self.name,
            " ".join(self.aliases),
            " ".join(self.addresses),
            " ".join(self.countries),
            " ".join(self.programs),
            self.remarks,
        ]
        return " ".join(p for p in parts if p)


class CSLIngestor:
    """Ingest the Consolidated Screening List."""

    def __init__(self, db: SanctionsDBService, download_dir: Path | None = None):
        """
        Initialize the CSL ingestor.

        Args:
            db: Sanctions database service.
            download_dir: Directory for downloaded files.
        """
        self.db = db
        self.download_dir = download_dir or Path("./data/downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def download_csl(self, force: bool = False) -> Path | None:
        """
        Download the Consolidated Screening List.

        Tries OpenSanctions first (more reliable), then official sources.

        Args:
            force: If True, download even if cached file exists.

        Returns:
            Path to downloaded JSON file, or None if all sources failed.
        """
        output_path = self.download_dir / "csl.json"

        if not force and output_path.exists():
            logger.info(f"Using cached CSL file: {output_path}")
            return output_path

        # Try sources in order of reliability
        sources_to_try = [
            ("opensanctions", CSL_SOURCES["opensanctions"]),
            ("trade_gov_json", CSL_SOURCES["trade_gov_json"]),
        ]

        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            for source_name, url in sources_to_try:
                try:
                    logger.info(f"Downloading CSL from {source_name}...")
                    response = await client.get(url)
                    response.raise_for_status()

                    output_path.write_bytes(response.content)
                    logger.info(
                        f"Downloaded CSL from {source_name} "
                        f"({len(response.content)} bytes)"
                    )
                    return output_path

                except Exception as e:
                    logger.warning(f"Failed to download from {source_name}: {e}")
                    continue

        logger.error("Failed to download CSL from all sources")
        return None

    def _parse_csl_json(self, json_path: Path) -> list[CSLEntry]:
        """Parse CSL JSON file into CSLEntry objects."""
        entries = []

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both OpenSanctions format (results array) and direct array
        results = data.get("results", data) if isinstance(data, dict) else data

        for item in results:
            try:
                entry = self._parse_csl_item(item)
                if entry:
                    entries.append(entry)
            except Exception as e:
                logger.warning(f"Error parsing CSL item: {e}")
                continue

        return entries

    def _parse_csl_item(self, item: dict[str, Any]) -> CSLEntry | None:
        """Parse a single CSL item."""
        name = item.get("name", "").strip()
        if not name:
            return None

        # Get ID
        entry_id = item.get("id") or item.get("entity_number") or ""
        if not entry_id:
            # Generate ID from name hash
            entry_id = f"CSL-{hash(name) % 100000:05d}"

        # Determine entry type
        entry_type_str = item.get("type", "").lower()
        if "individual" in entry_type_str:
            entry_type = EntityType.INDIVIDUAL
        elif "vessel" in entry_type_str:
            entry_type = EntityType.VESSEL
        elif "aircraft" in entry_type_str:
            entry_type = EntityType.AIRCRAFT
        else:
            entry_type = EntityType.ENTITY

        # Get source list
        source = item.get("source", "Unknown")
        source_code = self._map_source_to_code(source)

        # Get aliases
        aliases = item.get("alt_names", []) or []
        if isinstance(aliases, str):
            aliases = [aliases]

        # Parse addresses
        addresses = []
        countries = []
        for addr in item.get("addresses", []) or []:
            if isinstance(addr, dict):
                parts = []
                for field in ["address", "city", "state", "postal_code"]:
                    if addr.get(field):
                        parts.append(str(addr[field]))
                country = addr.get("country", "")
                if country:
                    parts.append(country)
                    if country not in countries:
                        countries.append(country)
                if parts:
                    addresses.append(", ".join(parts))
            elif isinstance(addr, str):
                addresses.append(addr)

        # Get programs
        programs = item.get("programs", []) or []
        if isinstance(programs, str):
            programs = [programs]

        # Get IDs
        ids = item.get("ids", []) or []

        # Get remarks
        remarks = item.get("remarks", "") or ""

        # Get source URL
        source_url = item.get("source_list_url", "") or ""

        # Get Federal Register citation
        fr_citation = item.get("federal_register_notice", "") or ""

        return CSLEntry(
            id=f"CSL-{entry_id}",
            name=name,
            entry_type=entry_type,
            source_list=source,
            source_list_code=source_code,
            programs=programs,
            aliases=aliases,
            addresses=addresses,
            countries=countries,
            ids=ids,
            remarks=remarks,
            source_url=source_url,
            federal_register_citation=fr_citation,
        )

    def _map_source_to_code(self, source: str) -> str:
        """Map source string to our internal code."""
        source_lower = source.lower()

        for full_name, code in CSL_SOURCE_MAPPING.items():
            if full_name.lower() in source_lower or source_lower in full_name.lower():
                return code

        # Fallback mappings
        if "denied" in source_lower:
            return "denied_persons"
        elif "entity" in source_lower:
            return "entity_list"
        elif "unverified" in source_lower:
            return "unverified_list"
        elif "meu" in source_lower or "military end" in source_lower:
            return "meu_list"
        elif "sdn" in source_lower or "specially designated" in source_lower:
            return "sdn"
        elif "cmic" in source_lower or "chinese military" in source_lower:
            return "ns_cmic"
        elif "capta" in source_lower or "561" in source_lower:
            return "capta"
        elif "itar" in source_lower or "debarred" in source_lower:
            return "itar_debarred"
        elif "nonprolif" in source_lower:
            return "nonproliferation"

        return "other"

    async def ingest(self, force_download: bool = False) -> dict[str, Any]:
        """
        Download and ingest the Consolidated Screening List.

        Args:
            force_download: If True, re-download even if cached.

        Returns:
            Dictionary with ingestion statistics.
        """
        result = {
            "source": "Consolidated Screening List",
            "entries_by_list": {},
            "total_entries": 0,
            "errors": [],
        }

        # Download CSL
        json_path = await self.download_csl(force=force_download)
        if not json_path:
            result["errors"].append("Failed to download CSL")
            return result

        # Parse entries
        try:
            entries = self._parse_csl_json(json_path)
            logger.info(f"Parsed {len(entries)} CSL entries")
        except Exception as e:
            result["errors"].append(f"Failed to parse CSL: {e}")
            return result

        # Store entries by list type
        list_counts: dict[str, int] = {}

        for entry in entries:
            try:
                # Store in appropriate table based on source
                self._store_entry(entry)

                # Track counts
                list_code = entry.source_list_code
                list_counts[list_code] = list_counts.get(list_code, 0) + 1
                result["total_entries"] += 1

            except Exception as e:
                if len(result["errors"]) < 10:
                    result["errors"].append(f"Error storing {entry.name}: {e}")

        # Add list-level statistics
        for code, count in list_counts.items():
            list_name = CSL_SOURCE_NAMES.get(code, code)
            result["entries_by_list"][list_name] = count

        return result

    def _store_entry(self, entry: CSLEntry) -> None:
        """Store a CSL entry in the appropriate database table."""
        # For now, store all CSL entries in a unified CSL table
        # The sanctions_db can be extended to support CSL-specific storage
        self.db.add_csl_entry(
            entry_id=entry.id,
            name=entry.name,
            entry_type=entry.entry_type.value,
            source_list=entry.source_list_code,
            programs=entry.programs,
            aliases=entry.aliases,
            addresses=entry.addresses,
            countries=entry.countries,
            remarks=entry.remarks,
        )


async def ingest_csl(
    db: SanctionsDBService,
    download_dir: Path | None = None,
    force_download: bool = False,
) -> dict[str, Any]:
    """
    Convenience function to ingest the CSL.

    Args:
        db: Sanctions database service.
        download_dir: Directory for downloads.
        force_download: If True, re-download.

    Returns:
        Ingestion result dictionary.
    """
    ingestor = CSLIngestor(db, download_dir)
    return await ingestor.ingest(force_download)
