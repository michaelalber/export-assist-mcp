#!/usr/bin/env python
"""Unified data ingestion script for Export Control MCP.

Downloads and ingests data from official government sources:
- EAR regulations from eCFR (15 CFR 730-774)
- ITAR regulations from eCFR (22 CFR 120-130)
- OFAC SDN List from Treasury
- BIS Denied Persons List from Commerce
- BIS Entity List (requires manual download)
- Consolidated Screening List (CSL) from OpenSanctions/Trade.gov

Usage:
    python scripts/ingest_all.py --all           # Ingest everything (regs + sanctions + CSL)
    python scripts/ingest_all.py --regulations   # EAR and ITAR from eCFR
    python scripts/ingest_all.py --sanctions     # SDN and Denied Persons
    python scripts/ingest_all.py --csl           # Consolidated Screening List (13 lists)
    python scripts/ingest_all.py --ear           # EAR only
    python scripts/ingest_all.py --itar          # ITAR only
    python scripts/ingest_all.py --sdn           # OFAC SDN only
    python scripts/ingest_all.py --denied        # BIS Denied Persons only
    python scripts/ingest_all.py --entity-list /path/to/entity_list.xlsx
    python scripts/ingest_all.py --sample        # Load sample data for testing
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from export_control_mcp.config import settings
from export_control_mcp.models.regulations import RegulationType
from export_control_mcp.services import (
    get_embedding_service,
    get_sanctions_db,
    get_vector_store,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def ingest_ear(force_download: bool = False) -> dict:
    """Ingest EAR from eCFR."""
    from export_control_mcp.data.ingest.ecfr_ingest import ECFRIngestor

    logger.info("Ingesting EAR from eCFR...")

    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    ingestor = ECFRIngestor(
        embedding_service,
        vector_store,
        regulation_type=RegulationType.EAR,
    )

    result = await ingestor.ingest_from_ecfr(force_download=force_download)

    logger.info(f"EAR ingestion complete: {result.chunks_created} chunks, {len(result.errors)} errors")

    return {
        "source": "EAR (eCFR)",
        "sections": result.sections_ingested,
        "chunks": result.chunks_created,
        "errors": result.errors,
    }


async def ingest_itar(force_download: bool = False) -> dict:
    """Ingest ITAR from eCFR."""
    from export_control_mcp.data.ingest.ecfr_ingest import ECFRIngestor

    logger.info("Ingesting ITAR from eCFR...")

    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    ingestor = ECFRIngestor(
        embedding_service,
        vector_store,
        regulation_type=RegulationType.ITAR,
    )

    result = await ingestor.ingest_from_ecfr(force_download=force_download)

    logger.info(f"ITAR ingestion complete: {result.chunks_created} chunks, {len(result.errors)} errors")

    return {
        "source": "ITAR (eCFR)",
        "sections": result.sections_ingested,
        "chunks": result.chunks_created,
        "errors": result.errors,
    }


async def ingest_ofac_sdn(force_download: bool = False) -> dict:
    """Ingest OFAC SDN List."""
    from export_control_mcp.data.ingest.sanctions_ingest import SanctionsIngestor

    logger.info("Ingesting OFAC SDN List...")

    db = get_sanctions_db()
    ingestor = SanctionsIngestor(db)

    result = await ingestor.ingest_ofac_sdn(force_download=force_download)

    logger.info(f"SDN ingestion complete: {result['entries_added']} entries, {len(result['errors'])} errors")

    return result


async def ingest_denied_persons(force_download: bool = False) -> dict:
    """Ingest BIS Denied Persons List."""
    from export_control_mcp.data.ingest.sanctions_ingest import SanctionsIngestor

    logger.info("Ingesting BIS Denied Persons List...")

    db = get_sanctions_db()
    ingestor = SanctionsIngestor(db)

    result = await ingestor.ingest_bis_denied_persons(force_download=force_download)

    logger.info(f"Denied Persons ingestion complete: {result['entries_added']} entries")

    return result


async def ingest_entity_list(excel_path: Path) -> dict:
    """Ingest BIS Entity List from Excel file."""
    from export_control_mcp.data.ingest.sanctions_ingest import SanctionsIngestor

    logger.info(f"Ingesting BIS Entity List from {excel_path}...")

    db = get_sanctions_db()
    ingestor = SanctionsIngestor(db)

    result = await ingestor.ingest_bis_entity_list(excel_path=excel_path)

    logger.info(f"Entity List ingestion complete: {result['entries_added']} entries")

    return result


async def ingest_csl(force_download: bool = False) -> dict:
    """Ingest Consolidated Screening List."""
    from export_control_mcp.data.ingest.csl_ingest import CSLIngestor

    logger.info("Ingesting Consolidated Screening List...")

    db = get_sanctions_db()
    # Clear existing CSL data
    db.clear_csl()

    ingestor = CSLIngestor(db)
    result = await ingestor.ingest(force_download=force_download)

    logger.info(f"CSL ingestion complete: {result['total_entries']} entries")

    return result


async def load_sample_data() -> dict:
    """Load sample data for testing."""
    # Import directly using sys.path which was set at the top of this file
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "update_sanctions",
        Path(__file__).parent / "update_sanctions.py"
    )
    update_sanctions = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(update_sanctions)

    logger.info("Loading sample data...")

    # Load sample sanctions data
    db = get_sanctions_db()
    update_sanctions.load_sample_data(db)

    # For regulations, we'd need sample EAR/ITAR chunks
    # For now, just return sanctions sample status
    stats = db.get_stats()

    return {
        "source": "Sample Data",
        "entity_list": stats.get("entity_list", 0),
        "sdn_list": stats.get("sdn_list", 0),
        "denied_persons": stats.get("denied_persons", 0),
        "country_sanctions": stats.get("country_sanctions", 0),
    }


async def ingest_all(force_download: bool = False) -> dict:
    """Ingest all data sources."""
    results = {}

    # Clear existing data
    logger.info("Clearing existing data...")
    vector_store = get_vector_store()
    vector_store.delete_all()
    db = get_sanctions_db()
    db.clear_all()

    # Ingest regulations
    results["ear"] = await ingest_ear(force_download)
    results["itar"] = await ingest_itar(force_download)

    # Ingest sanctions
    results["ofac_sdn"] = await ingest_ofac_sdn(force_download)
    results["denied_persons"] = await ingest_denied_persons(force_download)

    # Ingest Consolidated Screening List
    results["csl"] = await ingest_csl(force_download)

    # Load country sanctions data
    from export_control_mcp.tools.sanctions import COUNTRY_SANCTIONS_DATA
    for sanctions in COUNTRY_SANCTIONS_DATA.values():
        db.add_country_sanctions(sanctions)
    results["country_sanctions"] = {"loaded": len(COUNTRY_SANCTIONS_DATA)}

    # Summary
    total_chunks = sum(r.get("chunks", 0) for r in results.values())
    total_entries = sum(r.get("entries_added", 0) for r in results.values())
    total_errors = sum(len(r.get("errors", [])) for r in results.values())

    results["summary"] = {
        "total_regulation_chunks": total_chunks,
        "total_sanctions_entries": total_entries,
        "total_errors": total_errors,
    }

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest export control data from official sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/ingest_all.py --all              # Ingest everything
    python scripts/ingest_all.py --regulations      # EAR and ITAR only
    python scripts/ingest_all.py --sanctions        # SDN and Denied Persons
    python scripts/ingest_all.py --sample           # Load sample data
    python scripts/ingest_all.py --entity-list entity_list.xlsx

Data Sources:
    EAR:  https://www.ecfr.gov (15 CFR 730-774)
    ITAR: https://www.ecfr.gov (22 CFR 120-130)
    SDN:  https://www.treasury.gov/ofac/downloads/sdn.xml
    DPL:  https://www.bis.doc.gov/dpl/dpl.txt
        """,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Ingest all data sources (regulations + sanctions)",
    )
    parser.add_argument(
        "--regulations",
        action="store_true",
        help="Ingest EAR and ITAR from eCFR",
    )
    parser.add_argument(
        "--sanctions",
        action="store_true",
        help="Ingest SDN and Denied Persons lists",
    )
    parser.add_argument(
        "--ear",
        action="store_true",
        help="Ingest EAR only",
    )
    parser.add_argument(
        "--itar",
        action="store_true",
        help="Ingest ITAR only",
    )
    parser.add_argument(
        "--sdn",
        action="store_true",
        help="Ingest OFAC SDN List only",
    )
    parser.add_argument(
        "--denied",
        action="store_true",
        help="Ingest BIS Denied Persons List only",
    )
    parser.add_argument(
        "--entity-list",
        type=str,
        metavar="PATH",
        help="Path to BIS Entity List Excel file",
    )
    parser.add_argument(
        "--csl",
        action="store_true",
        help="Ingest Consolidated Screening List (13 combined screening lists)",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Load sample data for testing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if files exist",
    )
    parser.add_argument(
        "--output",
        type=str,
        metavar="PATH",
        help="Write results to JSON file",
    )

    args = parser.parse_args()

    # Check if any action specified
    if not any([
        args.all, args.regulations, args.sanctions,
        args.ear, args.itar, args.sdn, args.denied,
        args.entity_list, args.csl, args.sample,
    ]):
        parser.print_help()
        print("\nError: No action specified. Use --all, --regulations, --sanctions, etc.")
        sys.exit(1)

    # Run async ingestion
    async def run():
        results = {}

        if args.sample:
            results["sample"] = await load_sample_data()
        elif args.all:
            results = await ingest_all(args.force)
        else:
            if args.regulations or args.ear:
                results["ear"] = await ingest_ear(args.force)
            if args.regulations or args.itar:
                results["itar"] = await ingest_itar(args.force)
            if args.sanctions or args.sdn:
                results["ofac_sdn"] = await ingest_ofac_sdn(args.force)
            if args.sanctions or args.denied:
                results["denied_persons"] = await ingest_denied_persons(args.force)
            if args.entity_list:
                results["entity_list"] = await ingest_entity_list(Path(args.entity_list))
            if args.csl:
                results["csl"] = await ingest_csl(args.force)

        return results

    results = asyncio.run(run())

    # Print results
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(json.dumps(results, indent=2, default=str))

    # Write to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2, default=str))
        print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    main()
