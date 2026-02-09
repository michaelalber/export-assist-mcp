"""EAR (Export Administration Regulations) ingestion.

Handles downloading and parsing EAR content from the BIS website
or local PDF/HTML files.
"""

import logging
import re
from pathlib import Path

import httpx
from pypdf import PdfReader

from export_control_mcp.data.ingest.base import BaseIngestor, IngestResult
from export_control_mcp.models.regulations import RegulationChunk, RegulationType
from export_control_mcp.rag.chunking import ChunkMetadata, RegulationChunker

logger = logging.getLogger(__name__)

# BIS EAR download URLs (official sources)
EAR_SOURCES = {
    "ecfr": "https://www.ecfr.gov/api/versioner/v1/full/current/title-15.xml?chapter=VII&subchapter=C",
    "bis": "https://www.bis.doc.gov/index.php/regulations/export-administration-regulations-ear",
}

# EAR Part ranges and their titles
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


class EARIngestor(BaseIngestor):
    """Ingest EAR regulations from PDF or HTML sources."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize the EAR ingestor."""
        super().__init__(*args, **kwargs)
        self._chunker = RegulationChunker(max_tokens=512, overlap_tokens=50)

    @property
    def regulation_type(self) -> RegulationType:
        """Return EAR regulation type."""
        return RegulationType.EAR

    async def ingest(self, source_path: Path) -> IngestResult:
        """
        Ingest EAR content from a local file or directory.

        Args:
            source_path: Path to PDF file, HTML file, or directory of files.

        Returns:
            IngestResult with ingestion statistics.
        """
        result = self._create_result()

        if source_path.is_dir():
            # Process all PDFs and HTML files in directory
            files = list(source_path.glob("**/*.pdf")) + list(source_path.glob("**/*.html"))
            for file_path in files:
                try:
                    await self._process_file(file_path, result)
                except Exception as e:
                    result.errors.append(f"Error processing {file_path.name}: {e}")
                    logger.error(f"Failed to process {file_path}: {e}")
        elif source_path.suffix == ".pdf":
            await self._process_pdf(source_path, result)
        elif source_path.suffix in (".html", ".htm"):
            await self._process_html(source_path, result)
        else:
            result.errors.append(f"Unsupported file type: {source_path.suffix}")

        return result

    async def _process_file(self, file_path: Path, result: IngestResult) -> None:
        """Route file to appropriate processor."""
        if file_path.suffix == ".pdf":
            await self._process_pdf(file_path, result)
        elif file_path.suffix in (".html", ".htm"):
            await self._process_html(file_path, result)

    async def _process_pdf(self, pdf_path: Path, result: IngestResult) -> None:
        """Process a PDF file containing EAR content."""
        try:
            reader = PdfReader(pdf_path)
            full_text = ""

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"

            # Try to detect which EAR part this is
            part_number = self._detect_ear_part(pdf_path.stem, full_text)
            part_title = (
                EAR_PARTS.get(part_number, "Unknown Part") if part_number else "Unknown Part"
            )

            metadata = ChunkMetadata(
                part=f"Part {part_number}" if part_number else "Unknown",
                title=part_title,
                citation=f"15 CFR Part {part_number}" if part_number else "",
            )

            # Chunk the content
            chunks = self._chunker.chunk_text(
                full_text,
                metadata,
                RegulationType.EAR,
            )

            # Generate embeddings and store
            await self._store_chunks(chunks, result)

            result.sections_ingested += 1
            logger.info(f"Processed EAR PDF: {pdf_path.name} ({len(chunks)} chunks)")

        except Exception as e:
            result.errors.append(f"PDF processing error ({pdf_path.name}): {e}")
            logger.error(f"Failed to process PDF {pdf_path}: {e}")

    async def _process_html(self, html_path: Path, result: IngestResult) -> None:
        """Process an HTML file containing EAR content."""
        try:
            content = html_path.read_text(encoding="utf-8")

            # Simple HTML to text conversion (basic approach)
            # Remove script and style elements
            content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
            content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)

            # Remove HTML tags
            content = re.sub(r"<[^>]+>", " ", content)

            # Clean up whitespace
            content = re.sub(r"\s+", " ", content)
            content = content.strip()

            # Detect EAR part
            part_number = self._detect_ear_part(html_path.stem, content)
            part_title = (
                EAR_PARTS.get(part_number, "Unknown Part") if part_number else "Unknown Part"
            )

            metadata = ChunkMetadata(
                part=f"Part {part_number}" if part_number else "Unknown",
                title=part_title,
                citation=f"15 CFR Part {part_number}" if part_number else "",
            )

            chunks = self._chunker.chunk_text(
                content,
                metadata,
                RegulationType.EAR,
            )

            await self._store_chunks(chunks, result)

            result.sections_ingested += 1
            logger.info(f"Processed EAR HTML: {html_path.name} ({len(chunks)} chunks)")

        except Exception as e:
            result.errors.append(f"HTML processing error ({html_path.name}): {e}")
            logger.error(f"Failed to process HTML {html_path}: {e}")

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

    def _detect_ear_part(self, filename: str, content: str) -> int | None:
        """Try to detect which EAR part a document covers."""
        # Check filename first (e.g., "part730.pdf", "ear_730.html")
        match = re.search(r"(?:part|ear)[-_]?(\d{3})", filename.lower())
        if match:
            return int(match.group(1))

        # Check content for part references
        match = re.search(r"Part\s+(\d{3})\s*[-–—]\s*", content)
        if match:
            return int(match.group(1))

        # Check for CFR citation
        match = re.search(r"15\s*CFR\s*(?:Part\s*)?(\d{3})", content)
        if match:
            return int(match.group(1))

        return None

    async def download_from_ecfr(self, output_dir: Path) -> Path | None:
        """
        Download current EAR from eCFR (Electronic Code of Federal Regulations).

        Args:
            output_dir: Directory to save downloaded content.

        Returns:
            Path to the downloaded file, or None if download failed.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "ear_current.xml"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(EAR_SOURCES["ecfr"])
                response.raise_for_status()

                output_file.write_bytes(response.content)
                logger.info(f"Downloaded EAR from eCFR to {output_file}")
                return output_file

        except Exception as e:
            logger.error(f"Failed to download EAR from eCFR: {e}")
            return None
