#!/usr/bin/env python
"""Update sanctions lists from official government sources.

This script downloads and ingests the latest sanctions data from:
- BIS Entity List (Commerce Department)
- OFAC SDN List (Treasury Department)
- BIS Denied Persons List (Commerce Department)

Usage:
    python scripts/update_sanctions.py [--all|--entity-list|--sdn|--denied-persons]
    python scripts/update_sanctions.py --sample  # Load sample data for testing
"""

import argparse
import json
import logging
from datetime import date
from pathlib import Path

# Add project root to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from export_control_mcp.models.sanctions import (
    CountrySanctions,
    DeniedPersonEntry,
    EntityListEntry,
    EntityType,
    SDNEntry,
)
from export_control_mcp.services.sanctions_db import SanctionsDBService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Sample data for testing and development
SAMPLE_ENTITY_LIST = [
    EntityListEntry(
        id="EL-001",
        name="Huawei Technologies Co., Ltd.",
        aliases=["Huawei", "华为"],
        addresses=["Shenzhen, China"],
        country="CN",
        license_requirement="For all items subject to the EAR",
        license_policy="Presumption of denial",
        federal_register_citation="84 FR 22961",
        effective_date=date(2019, 5, 16),
    ),
    EntityListEntry(
        id="EL-002",
        name="Semiconductor Manufacturing International Corporation (SMIC)",
        aliases=["SMIC", "中芯国际"],
        addresses=["Shanghai, China"],
        country="CN",
        license_requirement="For all items subject to the EAR",
        license_policy="Presumption of denial for advanced technology nodes",
        federal_register_citation="85 FR 83416",
        effective_date=date(2020, 12, 18),
    ),
    EntityListEntry(
        id="EL-003",
        name="Moscow Institute of Physics and Technology",
        aliases=["MIPT", "PhysTech"],
        addresses=["Dolgoprudny, Moscow Oblast, Russia"],
        country="RU",
        license_requirement="For all items subject to the EAR",
        license_policy="Presumption of denial",
        federal_register_citation="87 FR 12226",
        effective_date=date(2022, 3, 3),
    ),
    EntityListEntry(
        id="EL-004",
        name="Aerospace Research Institute",
        aliases=["ARI"],
        addresses=["Tehran, Iran"],
        country="IR",
        license_requirement="For all items subject to the EAR",
        license_policy="Presumption of denial",
        federal_register_citation="Example citation",
        effective_date=date(2020, 1, 15),
    ),
    EntityListEntry(
        id="EL-005",
        name="Korea Mining Development Trading Corporation",
        aliases=["KOMID"],
        addresses=["Pyongyang, North Korea"],
        country="KP",
        license_requirement="For all items subject to the EAR",
        license_policy="Presumption of denial",
        federal_register_citation="Example citation",
        effective_date=date(2017, 6, 1),
    ),
]

SAMPLE_SDN_LIST = [
    SDNEntry(
        id="SDN-001",
        name="BANK MELLI IRAN",
        sdn_type=EntityType.ENTITY,
        programs=["IRAN", "IFSR"],
        aliases=["Bank Melli", "BMI"],
        addresses=["Ferdowsi Avenue, Tehran, Iran"],
        remarks="State-owned bank of Iran",
    ),
    SDNEntry(
        id="SDN-002",
        name="RUSSIAN DIRECT INVESTMENT FUND",
        sdn_type=EntityType.ENTITY,
        programs=["RUSSIA-EO14024", "UKRAINE-EO13660"],
        aliases=["RDIF"],
        addresses=["Moscow, Russia"],
        remarks="Russian sovereign wealth fund",
    ),
    SDNEntry(
        id="SDN-003",
        name="DERIPASKA, Oleg Vladimirovich",
        sdn_type=EntityType.INDIVIDUAL,
        programs=["RUSSIA-EO14024", "UKRAINE-EO13660"],
        aliases=["DERIPASKA, Oleg"],
        nationalities=["Russia"],
        dates_of_birth=["02 Jan 1968"],
        remarks="Russian oligarch",
    ),
    SDNEntry(
        id="SDN-004",
        name="MADURO MOROS, Nicolas",
        sdn_type=EntityType.INDIVIDUAL,
        programs=["VENEZUELA"],
        aliases=["MADURO, Nicolas"],
        nationalities=["Venezuela"],
        remarks="President of Venezuela",
    ),
    SDNEntry(
        id="SDN-005",
        name="ISLAMIC REVOLUTIONARY GUARD CORPS",
        sdn_type=EntityType.ENTITY,
        programs=["IRAN", "IRGC", "SDGT"],
        aliases=["IRGC", "Sepah-e Pasdaran"],
        addresses=["Iran"],
        remarks="Iranian military organization designated as FTO",
    ),
]

SAMPLE_DENIED_PERSONS = [
    DeniedPersonEntry(
        id="DP-001",
        name="John Smith",
        addresses=["123 Main St, Any City, USA"],
        effective_date=date(2020, 1, 15),
        expiration_date=date(2030, 1, 15),
        federal_register_citation="Example FR citation",
    ),
    DeniedPersonEntry(
        id="DP-002",
        name="Acme Export Corp",
        addresses=["456 Trade Ave, Commerce City, USA"],
        effective_date=date(2019, 6, 1),
        expiration_date=date(2029, 6, 1),
        federal_register_citation="Example FR citation",
    ),
]


def load_sample_data(db: SanctionsDBService) -> None:
    """Load sample data for testing and development."""
    logger.info("Loading sample sanctions data...")

    # Load Entity List
    for entry in SAMPLE_ENTITY_LIST:
        db.add_entity_list_entry(entry)
    logger.info(f"Loaded {len(SAMPLE_ENTITY_LIST)} Entity List entries")

    # Load SDN List
    for entry in SAMPLE_SDN_LIST:
        db.add_sdn_entry(entry)
    logger.info(f"Loaded {len(SAMPLE_SDN_LIST)} SDN List entries")

    # Load Denied Persons
    for entry in SAMPLE_DENIED_PERSONS:
        db.add_denied_person(entry)
    logger.info(f"Loaded {len(SAMPLE_DENIED_PERSONS)} Denied Persons entries")

    # Load country sanctions from the tools module
    from export_control_mcp.tools.sanctions import COUNTRY_SANCTIONS_DATA

    for sanctions in COUNTRY_SANCTIONS_DATA.values():
        db.add_country_sanctions(sanctions)
    logger.info(f"Loaded {len(COUNTRY_SANCTIONS_DATA)} country sanctions profiles")

    # Print stats
    stats = db.get_stats()
    logger.info(f"Database stats: {json.dumps(stats, indent=2)}")


def download_entity_list() -> None:
    """Download Entity List from BIS.

    Official source: https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list
    """
    logger.info("Entity List download not yet implemented")
    logger.info("To implement: Parse CSV/XML from BIS website")
    # TODO: Implement actual download and parsing
    # The Entity List is available in various formats from BIS


def download_sdn_list() -> None:
    """Download SDN List from OFAC.

    Official source: https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists
    """
    logger.info("SDN List download not yet implemented")
    logger.info("To implement: Parse XML from OFAC website")
    # TODO: Implement actual download and parsing
    # OFAC provides SDN list in XML format at:
    # https://www.treasury.gov/ofac/downloads/sdn.xml


def download_denied_persons() -> None:
    """Download Denied Persons List from BIS.

    Official source: https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/denied-persons-list
    """
    logger.info("Denied Persons List download not yet implemented")
    logger.info("To implement: Parse from BIS website")
    # TODO: Implement actual download and parsing


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update sanctions lists from official sources"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Load sample data for testing",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all sanctions lists",
    )
    parser.add_argument(
        "--entity-list",
        action="store_true",
        help="Update Entity List only",
    )
    parser.add_argument(
        "--sdn",
        action="store_true",
        help="Update SDN List only",
    )
    parser.add_argument(
        "--denied-persons",
        action="store_true",
        help="Update Denied Persons List only",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/sanctions.db",
        help="Path to sanctions database",
    )

    args = parser.parse_args()

    # Initialize database
    db = SanctionsDBService(db_path=args.db_path)

    if args.sample:
        load_sample_data(db)
    elif args.all:
        download_entity_list()
        download_sdn_list()
        download_denied_persons()
    elif args.entity_list:
        download_entity_list()
    elif args.sdn:
        download_sdn_list()
    elif args.denied_persons:
        download_denied_persons()
    else:
        # Default: show help
        parser.print_help()
        print("\n\nTip: Use --sample to load sample data for testing")

    db.close()


if __name__ == "__main__":
    main()
