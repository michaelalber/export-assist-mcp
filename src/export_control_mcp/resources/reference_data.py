"""Static reference data for export control lookups.

This module contains curated reference data for:
- ECCN entries from the Commerce Control List
- USML categories from 22 CFR 121
- Country groups from EAR Part 740 Supplement 1
- Export control glossary terms
- Control reason codes
"""

from typing import Any

from export_control_mcp.models.regulations import ECCN, USMLCategory, USMLItem

# Control reason codes
CONTROL_REASONS = {
    "AT": "Anti-Terrorism",
    "CB": "Chemical & Biological Weapons",
    "CC": "Crime Control",
    "CW": "Chemical Weapons Convention",
    "EI": "Encryption Items",
    "FC": "Firearms Convention",
    "MT": "Missile Technology",
    "NS": "National Security",
    "NP": "Nuclear Nonproliferation",
    "RS": "Regional Stability",
    "SS": "Short Supply",
    "UN": "United Nations Embargo",
}

# Common license exceptions
LICENSE_EXCEPTIONS = {
    "LVS": {
        "name": "Shipments of Limited Value",
        "description": "Permits exports of limited value to most destinations",
        "cfr": "15 CFR 740.3",
    },
    "GBS": {
        "name": "Group B Countries",
        "description": "Permits exports to Country Group B countries",
        "cfr": "15 CFR 740.4",
    },
    "CIV": {
        "name": "Civil End-Users",
        "description": "Permits exports for civil end-use in eligible countries",
        "cfr": "15 CFR 740.5",
    },
    "TSR": {
        "name": "Technology and Software Restricted",
        "description": "Permits exports of technology and software for specific purposes",
        "cfr": "15 CFR 740.6",
    },
    "TMP": {
        "name": "Temporary Imports, Exports, and Reexports",
        "description": "Permits temporary exports for various purposes",
        "cfr": "15 CFR 740.9",
    },
    "RPL": {
        "name": "Servicing and Replacement of Parts and Equipment",
        "description": "Permits one-for-one replacement of parts and components",
        "cfr": "15 CFR 740.10",
    },
    "GOV": {
        "name": "Governments and International Organizations",
        "description": "Permits exports to U.S. government agencies and contractors",
        "cfr": "15 CFR 740.11",
    },
    "TSU": {
        "name": "Technology and Software Unrestricted",
        "description": "Permits export of publicly available technology and software",
        "cfr": "15 CFR 740.13",
    },
    "BAG": {
        "name": "Baggage",
        "description": "Permits exports of personal effects",
        "cfr": "15 CFR 740.14",
    },
    "AVS": {
        "name": "Aircraft, Vessels, and Spacecraft",
        "description": "Permits exports of equipment for aircraft, vessels, and spacecraft",
        "cfr": "15 CFR 740.15",
    },
    "APR": {
        "name": "Additional Permissive Reexports",
        "description": "Permits certain reexports from foreign countries",
        "cfr": "15 CFR 740.16",
    },
    "ENC": {
        "name": "Encryption Commodities, Software, and Technology",
        "description": "Permits exports of certain encryption items",
        "cfr": "15 CFR 740.17",
    },
    "STA": {
        "name": "Strategic Trade Authorization",
        "description": "Permits exports to certain allied countries",
        "cfr": "15 CFR 740.20",
    },
}

# Sample ECCN data (commonly referenced ECCNs)
# In production, this would be loaded from the full CCL database
ECCN_DATA: dict[str, dict[str, Any]] = {
    "0A501": {
        "title": "Firearms and related commodities",
        "description": "Firearms, ammunition, and related commodities as follows",
        "control_reasons": ["NS", "FC", "CC"],
        "license_exceptions": ["LVS", "TMP", "GBS"],
    },
    "1C350": {
        "title": "Chemicals that may be used as precursors for toxic chemical agents",
        "description": "Chemicals in concentrations of 95% weight or greater",
        "control_reasons": ["CB", "CW"],
        "license_exceptions": [],
    },
    "3A001": {
        "title": "Electronic components",
        "description": "General purpose electronic equipment, integrated circuits, and components",
        "control_reasons": ["NS", "MT", "NP"],
        "license_exceptions": ["LVS", "GBS", "CIV", "TSR"],
    },
    "3A002": {
        "title": "General purpose electronic equipment",
        "description": "Recording equipment and specially designed components",
        "control_reasons": ["NS", "AT"],
        "license_exceptions": ["LVS", "GBS"],
    },
    "3A991": {
        "title": "Electronic components not controlled by 3A001",
        "description": "Electronic devices and components not elsewhere specified",
        "control_reasons": ["AT"],
        "license_exceptions": ["LVS", "GBS", "CIV"],
    },
    "4A003": {
        "title": "Digital computers and related equipment",
        "description": "Digital computers, electronic assemblies, and related equipment",
        "control_reasons": ["NS", "AT"],
        "license_exceptions": ["LVS", "GBS", "CIV", "APP"],
    },
    "4D001": {
        "title": "Software for computers controlled by 4A",
        "description": "Software for development, production, or use of equipment in 4A",
        "control_reasons": ["NS", "AT"],
        "license_exceptions": ["TSR", "TSU"],
    },
    "5A002": {
        "title": "Information security systems and equipment",
        "description": "Systems, equipment, and components for information security",
        "control_reasons": ["NS", "AT", "EI"],
        "license_exceptions": ["ENC", "TSU"],
    },
    "5D002": {
        "title": "Information security software",
        "description": "Software for development, production, or use of 5A002 equipment",
        "control_reasons": ["NS", "AT", "EI"],
        "license_exceptions": ["TSU", "ENC"],
    },
    "5E002": {
        "title": "Information security technology",
        "description": "Technology for development, production, or use of 5A002 equipment",
        "control_reasons": ["NS", "AT", "EI"],
        "license_exceptions": ["TSR"],
    },
    "6A002": {
        "title": "Optical sensors",
        "description": "Optical sensors and optical equipment not controlled by 6A001",
        "control_reasons": ["NS", "MT", "CC"],
        "license_exceptions": ["LVS", "GBS", "CIV"],
    },
    "6A003": {
        "title": "Cameras and imaging systems",
        "description": "Cameras, systems, or equipment, and components therefor",
        "control_reasons": ["NS", "CC"],
        "license_exceptions": ["LVS", "GBS", "CIV"],
    },
    "7A003": {
        "title": "Inertial navigation systems",
        "description": "Inertial navigation systems and specially designed components",
        "control_reasons": ["NS", "MT"],
        "license_exceptions": ["LVS", "GBS"],
    },
    "9A004": {
        "title": "Space launch vehicles and spacecraft",
        "description": "Space launch vehicles and spacecraft, and components",
        "control_reasons": ["NS", "MT", "NP"],
        "license_exceptions": [],
    },
    "9E003": {
        "title": "Technology for development of gas turbine engines",
        "description": "Technology for development, production, or overhaul of gas turbine engines",
        "control_reasons": ["NS", "MT"],
        "license_exceptions": [],
    },
}


def get_eccn(eccn_str: str) -> ECCN | None:
    """
    Look up an ECCN from the reference data.

    Args:
        eccn_str: ECCN string (e.g., "3A001", "5A002")

    Returns:
        ECCN object with details, or None if not found
    """
    try:
        eccn = ECCN.parse(eccn_str)
    except ValueError:
        return None

    # Look up additional data
    data = ECCN_DATA.get(eccn.raw)
    if data:
        eccn.title = data.get("title", "")
        eccn.description = data.get("description", "")
        eccn.control_reasons = data.get("control_reasons", [])
        eccn.license_exceptions = data.get("license_exceptions", [])

    return eccn


# USML Categories (22 CFR 121)
USML_CATEGORIES: dict[int, dict[str, Any]] = {
    1: {
        "title": "Firearms, Close Assault Weapons and Combat Shotguns",
        "description": "Nonautomatic and semi-automatic firearms to caliber .50 inclusive, combat shotguns, and silencers, flash suppressors, and specially designed components.",
        "sme": True,
        "items": [
            ("(a)", "Nonautomatic and semi-automatic firearms to caliber .50 inclusive"),
            ("(b)", "Combat shotguns"),
            ("(c)", "Silencers, mufflers, and sound suppressors"),
            ("(d)", "Riflescopes manufactured to military specifications"),
        ],
    },
    2: {
        "title": "Guns and Armament",
        "description": "Guns over caliber .50, howitzers, mortars, and related ammunition and components.",
        "sme": True,
        "items": [
            ("(a)", "Guns over caliber .50, howitzers, mortars, recoilless rifles"),
            ("(b)", "Flame throwers"),
            ("(c)", "Kinetic energy weapon systems"),
        ],
    },
    3: {
        "title": "Ammunition/Ordnance",
        "description": "Ammunition, propellant, incendiary agents, and related items.",
        "sme": True,
        "items": [
            ("(a)", "Ammunition for articles in Categories I and II"),
            ("(b)", "Bombs, grenades, torpedoes, depth charges"),
            ("(c)", "Mines"),
        ],
    },
    4: {
        "title": "Launch Vehicles, Guided Missiles, Ballistic Missiles, Rockets, Torpedoes, Bombs, and Mines",
        "description": "Launch vehicles, missiles, rockets, and related systems and equipment.",
        "sme": True,
        "items": [
            ("(a)", "Launch vehicles and missile systems"),
            ("(b)", "Individual rocket systems capable of delivering payload"),
            ("(c)", "Man-portable air defense systems (MANPADS)"),
        ],
    },
    5: {
        "title": "Explosives and Energetic Materials, Propellants, Incendiary Agents and Their Constituents",
        "description": "Explosive materials, propellants, and incendiary agents.",
        "sme": True,
        "items": [
            ("(a)", "Explosive compounds and mixtures"),
            ("(b)", "Propellants and propellant chemicals"),
            ("(c)", "Incendiary agents"),
        ],
    },
    6: {
        "title": "Surface Vessels of War and Special Naval Equipment",
        "description": "Warships, naval armament, and related equipment.",
        "sme": True,
        "items": [
            ("(a)", "Combatant vessels"),
            ("(b)", "Warship hull designs and special equipment"),
            ("(c)", "Naval nuclear propulsion equipment"),
        ],
    },
    7: {
        "title": "Ground Vehicles",
        "description": "Military vehicles, tanks, and related items.",
        "sme": True,
        "items": [
            ("(a)", "Military-type armed or armored vehicles"),
            ("(b)", "Military tanks"),
            ("(c)", "Bridge-launching vehicles"),
        ],
    },
    8: {
        "title": "Aircraft and Related Articles",
        "description": "Military aircraft, helicopters, unmanned aerial vehicles, and components.",
        "sme": True,
        "items": [
            ("(a)", "Aircraft designed for military use"),
            ("(b)", "Unmanned aerial vehicles (UAVs) for military use"),
            ("(c)", "Engines and engine parts for military aircraft"),
        ],
    },
    9: {
        "title": "Military Training Equipment and Training",
        "description": "Training equipment, simulators, and training services.",
        "sme": False,
        "items": [
            ("(a)", "Training devices and equipment"),
            ("(b)", "Simulators for defense articles"),
            ("(c)", "Operational flight trainers"),
        ],
    },
    10: {
        "title": "Personal Protective Equipment",
        "description": "Body armor, helmets, and protective equipment.",
        "sme": False,
        "items": [
            ("(a)", "Body armor and protective garments"),
            ("(b)", "Military helmets and helmet components"),
            ("(c)", "Combat boots"),
        ],
    },
    11: {
        "title": "Military Electronics",
        "description": "Military electronics, radar, and electronic warfare equipment.",
        "sme": True,
        "items": [
            ("(a)", "Electronic combat and radar equipment"),
            ("(b)", "Electronic warfare systems"),
            ("(c)", "Active denial systems"),
        ],
    },
    12: {
        "title": "Fire Control, Range Finder, Optical and Guidance and Control Equipment",
        "description": "Fire control systems, targeting systems, and guidance equipment.",
        "sme": True,
        "items": [
            ("(a)", "Fire control systems"),
            ("(b)", "Range finders and targeting systems"),
            ("(c)", "Inertial navigation systems for missiles"),
        ],
    },
    13: {
        "title": "Materials and Miscellaneous Articles",
        "description": "Armor, reactive materials, and miscellaneous military items.",
        "sme": False,
        "items": [
            ("(a)", "Metallic or non-metallic armor plate"),
            ("(b)", "Construction equipment built to military specifications"),
            ("(c)", "Ablative materials for military systems"),
        ],
    },
    14: {
        "title": "Toxicological Agents, Including Chemical Agents, Biological Agents, and Associated Equipment",
        "description": "Chemical and biological agents and delivery systems.",
        "sme": True,
        "items": [
            ("(a)", "Chemical agents"),
            ("(b)", "Biological agents"),
            ("(c)", "Equipment for dissemination of agents"),
        ],
    },
    15: {
        "title": "Spacecraft and Related Articles",
        "description": "Spacecraft, satellites, and ground control equipment.",
        "sme": True,
        "items": [
            ("(a)", "Spacecraft and satellites"),
            ("(b)", "Ground control equipment for spacecraft"),
            ("(c)", "Space-qualified electronics"),
        ],
    },
    16: {
        "title": "Nuclear Weapons Related Articles",
        "description": "Nuclear weapons, nuclear reactors for military use, and related items.",
        "sme": True,
        "items": [
            ("(a)", "Nuclear weapons and nuclear explosive devices"),
            ("(b)", "Nuclear reactors for military application"),
            ("(c)", "Components for nuclear weapons"),
        ],
    },
    17: {
        "title": "Classified Articles, Technical Data and Defense Services Not Otherwise Enumerated",
        "description": "Classified defense articles not covered in other categories.",
        "sme": True,
        "items": [
            ("(a)", "Classified articles not otherwise enumerated"),
            ("(b)", "Classified technical data"),
        ],
    },
    18: {
        "title": "Directed Energy Weapons",
        "description": "Directed energy weapons including lasers and particle beam systems.",
        "sme": True,
        "items": [
            ("(a)", "High energy laser systems"),
            ("(b)", "Particle beam systems"),
            ("(c)", "High-powered microwave systems"),
        ],
    },
    19: {
        "title": "Gas Turbine Engines and Associated Equipment",
        "description": "Military gas turbine engines and components.",
        "sme": True,
        "items": [
            ("(a)", "Gas turbine engines for military aircraft"),
            ("(b)", "Hot section components"),
            ("(c)", "Engine control systems"),
        ],
    },
    20: {
        "title": "Submersible Vessels and Related Articles",
        "description": "Submersible vessels, undersea systems, and diving equipment.",
        "sme": True,
        "items": [
            ("(a)", "Submersible vessels for military use"),
            ("(b)", "Swimmer delivery vehicles"),
            ("(c)", "Closed-circuit breathing apparatus"),
        ],
    },
    21: {
        "title": "Articles, Technical Data, and Defense Services Not Otherwise Enumerated",
        "description": "Catch-all category for defense articles not in other categories.",
        "sme": False,
        "items": [
            ("(a)", "Defense articles not enumerated in other categories"),
            ("(b)", "Technical data directly related to items in this category"),
        ],
    },
}


def get_usml_category(category: int | str) -> USMLCategory | None:
    """
    Look up a USML category from the reference data.

    Args:
        category: Category number (1-21) or Roman numeral (I-XXI)

    Returns:
        USMLCategory object with details, or None if not found
    """
    try:
        usml = USMLCategory.from_number(category)
    except ValueError:
        return None

    data = USML_CATEGORIES.get(usml.number_arabic)
    if data:
        usml.title = data.get("title", "")
        usml.description = data.get("description", "")
        usml.significant_military_equipment = data.get("sme", False)
        usml.items = [
            USMLItem(designation=item[0], description=item[1]) for item in data.get("items", [])
        ]

    return usml


# EAR Country Groups (15 CFR 740 Supplement No. 1)
COUNTRY_GROUPS: dict[str, dict[str, Any]] = {
    "A:1": {
        "name": "Wassenaar Arrangement",
        "description": "Participating states of the Wassenaar Arrangement",
        "countries": [
            "Argentina",
            "Australia",
            "Austria",
            "Belgium",
            "Bulgaria",
            "Canada",
            "Croatia",
            "Czech Republic",
            "Denmark",
            "Estonia",
            "Finland",
            "France",
            "Germany",
            "Greece",
            "Hungary",
            "India",
            "Ireland",
            "Italy",
            "Japan",
            "Latvia",
            "Lithuania",
            "Luxembourg",
            "Malta",
            "Mexico",
            "Netherlands",
            "New Zealand",
            "Norway",
            "Poland",
            "Portugal",
            "Romania",
            "Slovakia",
            "Slovenia",
            "South Africa",
            "South Korea",
            "Spain",
            "Sweden",
            "Switzerland",
            "Turkey",
            "Ukraine",
            "United Kingdom",
        ],
    },
    "A:5": {
        "name": "U.S. Arms Embargo (ITAR)",
        "description": "Countries subject to U.S. arms embargo for ITAR purposes",
        "countries": [
            "Belarus",
            "Burma",
            "China",
            "Cuba",
            "Iran",
            "North Korea",
            "Russia",
            "Syria",
            "Venezuela",
        ],
    },
    "A:6": {
        "name": "NATO Members",
        "description": "Members of the North Atlantic Treaty Organization",
        "countries": [
            "Albania",
            "Belgium",
            "Bulgaria",
            "Canada",
            "Croatia",
            "Czech Republic",
            "Denmark",
            "Estonia",
            "Finland",
            "France",
            "Germany",
            "Greece",
            "Hungary",
            "Iceland",
            "Italy",
            "Latvia",
            "Lithuania",
            "Luxembourg",
            "Montenegro",
            "Netherlands",
            "North Macedonia",
            "Norway",
            "Poland",
            "Portugal",
            "Romania",
            "Slovakia",
            "Slovenia",
            "Spain",
            "Sweden",
            "Turkey",
            "United Kingdom",
        ],
    },
    "B": {
        "name": "Chemical & Biological",
        "description": "Countries subject to chemical and biological weapons controls",
        "countries": ["All countries except Country Group A:5"],
    },
    "D:1": {
        "name": "National Security",
        "description": "Countries of national security concern",
        "countries": [
            "Afghanistan",
            "Armenia",
            "Azerbaijan",
            "Belarus",
            "Burma",
            "Cambodia",
            "China",
            "Cyprus",
            "Egypt",
            "Georgia",
            "Hong Kong",
            "India",
            "Iraq",
            "Israel",
            "Jordan",
            "Kazakhstan",
            "Kuwait",
            "Laos",
            "Lebanon",
            "Libya",
            "Macau",
            "Moldova",
            "Mongolia",
            "Oman",
            "Pakistan",
            "Qatar",
            "Russia",
            "Saudi Arabia",
            "Tajikistan",
            "Turkmenistan",
            "Ukraine",
            "United Arab Emirates",
            "Uzbekistan",
            "Vietnam",
            "Yemen",
        ],
    },
    "D:2": {
        "name": "Nuclear Concerns",
        "description": "Countries of nuclear proliferation concern",
        "countries": [
            "Afghanistan",
            "Algeria",
            "Armenia",
            "Azerbaijan",
            "Belarus",
            "Burma",
            "China",
            "Georgia",
            "India",
            "Iraq",
            "Israel",
            "Jordan",
            "Kazakhstan",
            "Lebanon",
            "Libya",
            "Macau",
            "Moldova",
            "Mongolia",
            "North Korea",
            "Pakistan",
            "Russia",
            "Syria",
            "Tajikistan",
            "Turkmenistan",
            "Ukraine",
            "Uzbekistan",
            "Vietnam",
        ],
    },
    "D:3": {
        "name": "Chemical & Biological Concerns",
        "description": "Countries of chemical and biological weapons concern",
        "countries": [
            "Armenia",
            "Azerbaijan",
            "Belarus",
            "Burma",
            "Cambodia",
            "China",
            "Georgia",
            "Iraq",
            "Kazakhstan",
            "Laos",
            "Moldova",
            "Mongolia",
            "North Korea",
            "Pakistan",
            "Russia",
            "Syria",
            "Tajikistan",
            "Turkmenistan",
            "Ukraine",
            "Uzbekistan",
            "Vietnam",
        ],
    },
    "D:4": {
        "name": "Missile Technology Concerns",
        "description": "Countries of missile technology proliferation concern",
        "countries": [
            "Afghanistan",
            "Armenia",
            "Azerbaijan",
            "Belarus",
            "Burma",
            "China",
            "Georgia",
            "India",
            "Iran",
            "Iraq",
            "Israel",
            "Kazakhstan",
            "Libya",
            "Moldova",
            "Mongolia",
            "North Korea",
            "Pakistan",
            "Russia",
            "Syria",
            "Tajikistan",
            "Turkmenistan",
            "Ukraine",
            "Uzbekistan",
        ],
    },
    "D:5": {
        "name": "U.S. Arms Embargo (EAR)",
        "description": "Countries subject to arms embargo for EAR purposes",
        "countries": [
            "Belarus",
            "Burma",
            "China",
            "Cuba",
            "Iran",
            "North Korea",
            "Russia",
            "Syria",
            "Venezuela",
        ],
    },
    "E:1": {
        "name": "Terrorist Supporting Countries",
        "description": "Countries designated as supporting terrorism",
        "countries": ["Cuba", "Iran", "North Korea", "Syria"],
    },
    "E:2": {
        "name": "Unilateral Embargo",
        "description": "Countries subject to comprehensive U.S. embargo",
        "countries": ["Cuba", "North Korea"],
    },
}


def get_country_groups(country: str) -> list[str]:
    """
    Get all country groups that include a given country.

    Args:
        country: Country name (case-insensitive)

    Returns:
        List of country group codes the country belongs to
    """
    country_lower = country.lower().strip()
    groups = []

    for group_code, group_data in COUNTRY_GROUPS.items():
        countries = group_data.get("countries", [])
        if isinstance(countries, list):
            for c in countries:
                if c.lower() == country_lower:
                    groups.append(group_code)
                    break

    return groups


# Export control glossary
GLOSSARY: dict[str, dict[str, Any]] = {
    "deemed export": {
        "definition": "Release of technology or source code subject to the EAR to a foreign national in the United States. Such release is 'deemed' to be an export to the home country of the foreign national.",
        "regulation": "15 CFR 734.13",
        "related_terms": ["foreign national", "technology", "source code"],
    },
    "end-user": {
        "definition": "The person abroad that receives and ultimately uses the exported or reexported items. The end-user is not an intermediate consignee.",
        "regulation": "15 CFR 772.1",
        "related_terms": ["ultimate consignee", "intermediate consignee"],
    },
    "fundamental research": {
        "definition": "Basic and applied research in science and engineering, the results of which ordinarily are published and shared broadly within the scientific community.",
        "regulation": "15 CFR 734.8",
        "related_terms": ["publicly available", "educational information"],
    },
    "published": {
        "definition": "Information that is published or will be published, is or will be generally accessible to the interested public, and is available without restrictions upon further dissemination.",
        "regulation": "15 CFR 734.7",
        "related_terms": ["publicly available", "fundamental research"],
    },
    "reexport": {
        "definition": "An actual shipment or transmission of items subject to the EAR from one foreign country to another foreign country.",
        "regulation": "15 CFR 734.14",
        "related_terms": ["export", "transfer (in-country)"],
    },
    "technology": {
        "definition": "Specific information necessary for the development, production, operation, installation, maintenance, repair, overhaul, or refurbishing of an item.",
        "regulation": "15 CFR 772.1",
        "related_terms": ["technical data", "source code"],
    },
    "defense article": {
        "definition": "Any item or technical data designated in the United States Munitions List (USML) at 22 CFR 121.1.",
        "regulation": "22 CFR 120.31",
        "related_terms": ["defense service", "technical data", "USML"],
    },
    "defense service": {
        "definition": "Furnishing of assistance, including training, to foreign persons in the design, development, engineering, manufacture, production, assembly, testing, repair, maintenance, modification, operation, demilitarization, destruction, processing, or use of defense articles.",
        "regulation": "22 CFR 120.32",
        "related_terms": ["defense article", "foreign person", "technical data"],
    },
    "foreign person": {
        "definition": "Any natural person who is not a lawful permanent resident or a protected individual under 8 USC 1324b(a)(3). Also includes foreign corporations, governments, and international organizations.",
        "regulation": "22 CFR 120.62",
        "related_terms": ["U.S. person", "foreign national"],
    },
    "technical data": {
        "definition": "Information required for the design, development, production, manufacture, assembly, operation, repair, testing, maintenance, or modification of defense articles.",
        "regulation": "22 CFR 120.33",
        "related_terms": ["defense article", "technology"],
    },
    "EAR99": {
        "definition": "Items subject to the EAR that are not listed on the Commerce Control List. These items generally can be exported without a license to most destinations, end-users, and end-uses.",
        "regulation": "15 CFR 734.3",
        "related_terms": ["ECCN", "NLR", "Commerce Control List"],
    },
    "NLR": {
        "definition": "No License Required. A license exception symbol indicating that no license is required for the export or reexport.",
        "regulation": "15 CFR Part 758",
        "related_terms": ["EAR99", "license exception"],
    },
}


def get_glossary_term(term: str) -> dict[str, Any] | None:
    """
    Look up a glossary term.

    Args:
        term: Term to look up (case-insensitive)

    Returns:
        Dictionary with definition and related info, or None if not found
    """
    term_lower = term.lower().strip()

    # Direct lookup
    if term_lower in GLOSSARY:
        entry = GLOSSARY[term_lower]
        return {
            "term": term_lower,
            "definition": entry["definition"],
            "regulation": entry.get("regulation", ""),
            "related_terms": entry.get("related_terms", []),
        }

    # Fuzzy match - check if term is contained in any key
    for key, entry in GLOSSARY.items():
        if term_lower in key or key in term_lower:
            return {
                "term": key,
                "definition": entry["definition"],
                "regulation": entry.get("regulation", ""),
                "related_terms": entry.get("related_terms", []),
            }

    return None
