#!/usr/bin/env python3
"""Script to ingest export control regulations into the vector store.

Usage:
    # Ingest EAR from local files
    uv run python scripts/ingest_regulations.py --source ./data/regulations/ear/

    # Download and ingest EAR from eCFR
    uv run python scripts/ingest_regulations.py --download --type ear

    # Ingest ITAR from local files
    uv run python scripts/ingest_regulations.py --source ./data/regulations/itar/ --type itar
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from export_control_mcp.config import settings
from export_control_mcp.data.ingest.ear_ingest import EARIngestor
from export_control_mcp.services import get_embedding_service, get_vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> int:
    """Run the ingestion pipeline."""
    parser = argparse.ArgumentParser(
        description="Ingest export control regulations into vector store",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Path to source file or directory containing regulation files",
    )
    parser.add_argument(
        "--type",
        choices=["ear", "itar"],
        default="ear",
        help="Type of regulations to ingest (default: ear)",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download latest regulations from official sources",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./data/regulations"),
        help="Directory for downloaded files (default: ./data/regulations)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before ingestion",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.download and not args.source:
        parser.error("Either --source or --download must be specified")

    # Initialize services
    logger.info("Initializing services...")
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    # Clear existing data if requested
    if args.clear:
        logger.warning("Clearing existing regulation data...")
        from export_control_mcp.models.regulations import RegulationType

        reg_type = RegulationType.EAR if args.type == "ear" else RegulationType.ITAR
        vector_store.delete_all(reg_type)
        logger.info("Existing data cleared")

    # Create ingestor
    if args.type == "ear":
        ingestor = EARIngestor(
            embedding_service=embedding_service,
            vector_store=vector_store,
        )
    else:
        # ITAR ingestor not yet implemented
        logger.error("ITAR ingestion not yet implemented")
        return 1

    # Download if requested
    source_path = args.source
    if args.download:
        logger.info("Downloading regulations from official sources...")
        output_dir = args.output_dir / args.type
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.type == "ear":
            downloaded = await ingestor.download_from_ecfr(output_dir)
            if downloaded:
                source_path = output_dir
            else:
                logger.error("Download failed")
                return 1
        else:
            logger.error("ITAR download not yet implemented")
            return 1

    # Run ingestion
    logger.info(f"Ingesting {args.type.upper()} from {source_path}...")
    result = await ingestor.ingest(source_path)

    # Report results
    print("\n" + "=" * 50)
    print("INGESTION RESULTS")
    print("=" * 50)
    print(f"Regulation Type: {result.regulation_type.upper()}")
    print(f"Sections Ingested: {result.sections_ingested}")
    print(f"Chunks Created: {result.chunks_created}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")

    if result.success:
        print("\n✓ Ingestion completed successfully!")
        return 0
    else:
        print("\n✗ Ingestion failed - no content was processed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
