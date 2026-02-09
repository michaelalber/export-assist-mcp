"""eCFR (Electronic Code of Federal Regulations) ingestion.

Downloads and parses export control regulations from the official eCFR API:
- EAR: 15 CFR 730-774 (Export Administration Regulations)
- ITAR: 22 CFR 120-130 (International Traffic in Arms Regulations)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec B405 - type annotation only

import defusedxml.ElementTree as ET  # noqa: N817 - ET is standard convention
import httpx

from export_control_mcp.data.ingest.base import BaseIngestor, IngestResult
from export_control_mcp.models.regulations import RegulationChunk, RegulationType
from export_control_mcp.rag.chunking import ChunkMetadata, RegulationChunker
from export_control_mcp.services.embeddings import EmbeddingService
from export_control_mcp.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


# eCFR API endpoints
# Note: The eCFR API changed format. Full title download uses /full/{date}/title-{num}.xml
# We download the full title and filter to relevant parts during parsing.
ECFR_API_BASE = "https://www.ecfr.gov/api/versioner/v1"

ECFR_SOURCES = {
    # EAR: Title 15 (we filter to Chapter VII, Subchapter C, Parts 730-774 during parsing)
    "ear_full": f"{ECFR_API_BASE}/full/current/title-15.xml",
    # ITAR: Title 22 (we filter to Chapter I, Subchapter M, Parts 120-130 during parsing)
    "itar_full": f"{ECFR_API_BASE}/full/current/title-22.xml",
    # Individual part endpoints (for targeted updates) - may not work with new API
    "ear_part": f"{ECFR_API_BASE}/full/current/title-15.xml",
    "itar_part": f"{ECFR_API_BASE}/full/current/title-22.xml",
}

# EAR Parts (15 CFR 730-774)
EAR_PARTS = {
    730: "General Information",
    732: "Steps for Using the EAR",
    734: "Scope of the Export Administration Regulations",
    736: "General Prohibitions",
    738: "Commerce Control List Overview and the Country Chart",
    740: "License Exceptions",
    742: "Control Policy - CCL Based Controls",
    743: "Special Reporting and Notification",
    744: "Control Policy: End-User and End-Use Based",
    745: "Chemical Weapons Convention Requirements",
    746: "Embargoes and Other Special Controls",
    748: "Applications (Classification, Advisory, and License)",
    750: "Application Processing, Issuance, and Denial",
    752: "Special Comprehensive License",
    754: "Short Supply Controls",
    756: "Appeals and Judicial Review",
    758: "Export Clearance Requirements and Authorities",
    760: "Restrictive Trade Practices or Boycotts",
    762: "Recordkeeping",
    764: "Enforcement and Protective Measures",
    766: "Administrative Enforcement Proceedings",
    768: "Foreign Availability Determination Procedures",
    770: "Interpretations",
    772: "Definitions of Terms",
    774: "The Commerce Control List",
}

# ITAR Parts (22 CFR 120-130)
ITAR_PARTS = {
    120: "Purpose and Definitions",
    121: "The United States Munitions List",
    122: "Registration of Manufacturers and Exporters",
    123: "Licenses for the Export and Temporary Import of Defense Articles",
    124: "Agreements, Off-Shore Procurement, and Other Defense Services",
    125: "Licenses for the Export of Technical Data and Classified Defense Articles",
    126: "General Policies and Provisions",
    127: "Violations and Penalties",
    128: "Administrative Procedures",
    129: "Registration and Licensing of Brokers",
    130: "Political Contributions, Fees and Commissions",
}


class ECFRIngestor(BaseIngestor):
    """Ingest regulations from the eCFR API."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStoreService,
        regulation_type: RegulationType = RegulationType.EAR,
        download_dir: Path | None = None,
        batch_size: int = 50,
    ):
        """
        Initialize the eCFR ingestor.

        Args:
            embedding_service: Service for generating embeddings.
            vector_store: Service for storing regulation chunks.
            regulation_type: EAR or ITAR.
            download_dir: Directory for downloaded files.
            batch_size: Number of chunks to process per batch.
        """
        super().__init__(embedding_service, vector_store, batch_size)
        self._regulation_type = regulation_type
        self.download_dir = download_dir or Path("./data/downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._chunker = RegulationChunker(max_tokens=512, overlap_tokens=50)

    @property
    def regulation_type(self) -> RegulationType:
        """Return the regulation type being ingested."""
        return self._regulation_type

    async def _get_latest_ecfr_date(self, client: httpx.AsyncClient) -> str | None:
        """Fetch the latest available date for eCFR content."""
        try:
            response = await client.get(f"{ECFR_API_BASE}/titles")
            response.raise_for_status()
            data = response.json()
            # Find the title we need (15 for EAR, 22 for ITAR)
            title_num = 15 if self._regulation_type == RegulationType.EAR else 22
            for title in data.get("titles", []):
                if title.get("number") == title_num:
                    result: str | None = title.get("up_to_date_as_of")
                    return result
            return None
        except Exception as e:
            logger.warning(f"Failed to get eCFR date: {e}")
            return None

    async def download_from_ecfr(self, force: bool = False) -> Path | None:
        """
        Download current regulations from eCFR.

        Args:
            force: If True, download even if file exists.

        Returns:
            Path to downloaded XML file, or None if failed.
        """
        if self._regulation_type == RegulationType.EAR:
            title_num = 15
            filename = "ear_current.xml"
        else:
            title_num = 22
            filename = "itar_current.xml"

        output_path = self.download_dir / filename

        if not force and output_path.exists():
            logger.info(f"Using cached file: {output_path}")
            return output_path

        try:
            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                # Get the latest available date
                latest_date = await self._get_latest_ecfr_date(client)
                if not latest_date:
                    logger.error("Could not determine latest eCFR date")
                    return None

                # Build URL with date (eCFR API requires specific date, not "current")
                url = f"{ECFR_API_BASE}/full/{latest_date}/title-{title_num}.xml"

                logger.info(
                    f"Downloading {self.regulation_name} from eCFR (as of {latest_date})..."
                )
                response = await client.get(url)
                response.raise_for_status()

                output_path.write_bytes(response.content)
                logger.info(f"Downloaded to {output_path} ({len(response.content)} bytes)")
                return output_path

        except Exception as e:
            logger.error(f"Failed to download from eCFR: {e}")
            return None

    async def ingest(self, source_path: Path) -> IngestResult:
        """
        Ingest regulation content from an XML file.

        Args:
            source_path: Path to eCFR XML file.

        Returns:
            IngestResult with ingestion statistics.
        """
        result = self._create_result()

        if not source_path.exists():
            result.errors.append(f"File not found: {source_path}")
            return result

        try:
            # Parse the eCFR XML
            chunks = self._parse_ecfr_xml(source_path)
            logger.info(f"Parsed {len(chunks)} chunks from {source_path.name}")

            # Store chunks in batches
            await self._store_chunks(chunks, result)

            result.sections_ingested = len({c.part for c in chunks})

        except Exception as e:
            result.errors.append(f"XML parsing error: {e}")
            logger.error(f"Failed to parse eCFR XML: {e}")

        return result

    async def ingest_from_ecfr(self, force_download: bool = False) -> IngestResult:
        """
        Download and ingest current regulations from eCFR.

        Args:
            force_download: If True, re-download even if cached.

        Returns:
            IngestResult with ingestion statistics.
        """
        # Download from eCFR
        xml_path = await self.download_from_ecfr(force=force_download)
        if not xml_path:
            result = self._create_result()
            result.errors.append("Failed to download from eCFR")
            return result

        return await self.ingest(xml_path)

    def _parse_ecfr_xml(self, xml_path: Path) -> list[RegulationChunk]:
        """Parse eCFR XML file into RegulationChunk objects."""
        chunks = []

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # eCFR XML structure varies; adapt to common patterns
        parts = self._get_parts_from_type()
        cfr_title = 15 if self._regulation_type == RegulationType.EAR else 22

        # Find all part elements
        for part_elem in root.iter("DIV5"):  # DIV5 is typically a Part
            part_num = self._extract_part_number(part_elem)
            if not part_num or part_num not in parts:
                continue

            part_title = parts.get(part_num, f"Part {part_num}")
            part_str = f"Part {part_num}"
            citation_base = f"{cfr_title} CFR Part {part_num}"

            # Extract sections within the part
            for section_elem in part_elem.iter("DIV8"):  # DIV8 is typically a Section
                section_num = self._extract_section_number(section_elem)
                section_title = self._extract_title(section_elem)
                section_text = self._extract_text(section_elem)

                if not section_text.strip():
                    continue

                citation = f"{cfr_title} CFR {section_num}" if section_num else citation_base

                metadata = ChunkMetadata(
                    part=part_str,
                    section=section_num,
                    title=section_title or part_title,
                    citation=citation,
                )

                # Chunk the section content
                section_chunks = self._chunker.chunk_text(
                    section_text,
                    metadata,
                    self._regulation_type,
                )
                chunks.extend(section_chunks)

        # If DIV5/DIV8 structure didn't work, try alternative parsing
        if not chunks:
            chunks = self._parse_ecfr_xml_alternative(root, parts, cfr_title)

        return chunks

    def _parse_ecfr_xml_alternative(
        self,
        root: Element,
        parts: dict[int, str],
        cfr_title: int,
    ) -> list[RegulationChunk]:
        """Alternative parsing for different eCFR XML structures."""
        chunks = []

        # Try finding parts by HEAD elements containing "PART"
        current_part = None
        current_text = []

        for elem in root.iter():
            if elem.tag == "HEAD" and elem.text:
                text = elem.text.strip()
                # Check if this is a part header
                part_match = re.search(r"PART\s+(\d+)", text, re.IGNORECASE)
                if part_match:
                    # Save previous part if exists
                    if current_part and current_text:
                        chunks.extend(
                            self._chunk_part_content(
                                current_part, parts, cfr_title, "\n".join(current_text)
                            )
                        )

                    current_part = int(part_match.group(1))
                    current_text = [text]
                elif current_part:
                    current_text.append(text)

            elif elem.tag == "P" and elem.text and current_part:
                # Paragraph content
                current_text.append(elem.text.strip())

        # Don't forget the last part
        if current_part and current_text:
            chunks.extend(
                self._chunk_part_content(current_part, parts, cfr_title, "\n".join(current_text))
            )

        return chunks

    def _chunk_part_content(
        self,
        part_num: int,
        parts: dict[int, str],
        cfr_title: int,
        content: str,
    ) -> list[RegulationChunk]:
        """Create chunks from part content."""
        if part_num not in parts:
            return []

        part_title = parts.get(part_num, f"Part {part_num}")
        metadata = ChunkMetadata(
            part=f"Part {part_num}",
            title=part_title,
            citation=f"{cfr_title} CFR Part {part_num}",
        )

        return self._chunker.chunk_text(content, metadata, self._regulation_type)

    def _get_parts_from_type(self) -> dict[int, str]:
        """Get parts dictionary based on regulation type."""
        return EAR_PARTS if self._regulation_type == RegulationType.EAR else ITAR_PARTS

    def _extract_part_number(self, elem: Element) -> int | None:
        """Extract part number from element."""
        # Check N attribute
        n_attr = elem.get("N", "")
        if n_attr:
            match = re.search(r"(\d+)", n_attr)
            if match:
                return int(match.group(1))

        # Check HEAD child
        head = elem.find("HEAD")
        if head is not None and head.text:
            match = re.search(r"PART\s+(\d+)", head.text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _extract_section_number(self, elem: Element) -> str | None:
        """Extract section number (e.g., '730.1')."""
        n_attr = elem.get("N", "")
        if n_attr:
            # Clean up the section number
            return n_attr.replace("§", "").strip()

        head = elem.find("HEAD")
        if head is not None and head.text:
            match = re.search(r"§?\s*(\d+\.\d+)", head.text)
            if match:
                return match.group(1)

        return None

    def _extract_title(self, elem: Element) -> str:
        """Extract title from element."""
        head = elem.find("HEAD")
        if head is not None and head.text:
            # Remove section number from title
            title = re.sub(r"^§?\s*\d+\.\d+\s*", "", head.text)
            return title.strip()
        return ""

    def _extract_text(self, elem: Element) -> str:
        """Extract all text content from element and children."""
        texts = []

        for child in elem.iter():
            if child.text:
                texts.append(child.text.strip())
            if child.tail:
                texts.append(child.tail.strip())

        return " ".join(texts)

    async def _store_chunks(
        self,
        chunks: list[RegulationChunk],
        result: IngestResult,
    ) -> None:
        """Generate embeddings and store chunks in batches."""
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]

            # Generate embeddings
            texts = [chunk.to_embedding_text() for chunk in batch]
            embeddings = self.embedding_service.embed_batch(texts)

            # Store in vector database
            self.vector_store.add_chunks_batch(batch, embeddings)

            result.chunks_created += len(batch)


async def ingest_all_regulations(
    embedding_service: EmbeddingService,
    vector_store: VectorStoreService,
    force_download: bool = False,
) -> dict[str, Any]:
    """
    Ingest both EAR and ITAR from eCFR.

    Args:
        embedding_service: Embedding service.
        vector_store: Vector store service.
        force_download: If True, re-download from eCFR.

    Returns:
        Dictionary with combined results.
    """
    results = {}

    # Clear existing regulation data
    logger.info("Clearing existing regulation data...")
    vector_store.delete_all()

    # Ingest EAR
    logger.info("Ingesting EAR from eCFR...")
    ear_ingestor = ECFRIngestor(embedding_service, vector_store, RegulationType.EAR)
    ear_result = await ear_ingestor.ingest_from_ecfr(force_download)
    results["ear"] = {
        "sections_ingested": ear_result.sections_ingested,
        "chunks_created": ear_result.chunks_created,
        "errors": ear_result.errors,
    }

    # Ingest ITAR
    logger.info("Ingesting ITAR from eCFR...")
    itar_ingestor = ECFRIngestor(embedding_service, vector_store, RegulationType.ITAR)
    itar_result = await itar_ingestor.ingest_from_ecfr(force_download)
    results["itar"] = {
        "sections_ingested": itar_result.sections_ingested,
        "chunks_created": itar_result.chunks_created,
        "errors": itar_result.errors,
    }

    # Summary
    results["summary"] = {
        "total_chunks": ear_result.chunks_created + itar_result.chunks_created,
        "total_sections": ear_result.sections_ingested + itar_result.sections_ingested,
        "total_errors": len(ear_result.errors) + len(itar_result.errors),
    }

    return results
