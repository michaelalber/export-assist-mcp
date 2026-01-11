# Export Control MCP Server

![CI](https://github.com/michaelalber/export-assist-mcp/actions/workflows/ci.yml/badge.svg?branch=main)
![Security](https://github.com/michaelalber/export-assist-mcp/actions/workflows/security.yml/badge.svg?branch=main)

MCP server providing AI assistant tools for export control compliance (EAR/ITAR/OFAC).

## Overview

A FastMCP-based Model Context Protocol server for National Laboratory Export Control groups. Provides semantic search over regulations, sanctions list screening, and AI-assisted classification guidance.

## Features

### Regulation Tools
- `search_ear` - Semantic search over Export Administration Regulations (15 CFR 730-774)
- `search_itar` - Semantic search over ITAR (22 CFR 120-130)
- `search_regulations` - Combined search across both EAR and ITAR
- `get_eccn_details` - Lookup specific ECCN details and control reasons
- `get_usml_category_details` - Lookup USML category details
- `compare_jurisdictions` - EAR vs ITAR jurisdiction analysis

### Sanctions Tools
- `search_consolidated_screening_list` - Search across 13 combined screening lists (CSL)
- `get_csl_statistics` - Database statistics by source list
- `check_country_sanctions` - Country-specific sanctions summary

CSL includes: SDN, Entity List, Denied Persons, Unverified List, MEU List, ITAR Debarred, Nonproliferation, FSE, SSI, CAPTA, NS-MBS, NS-CMIC, NS-PLC

Legacy tools (use CSL instead): `search_entity_list`, `search_sdn_list`, `search_denied_persons`

### DOE Nuclear Tools (10 CFR 810)
- `check_cfr810_country` - Check nuclear technology transfer authorization status
- `list_cfr810_countries` - List Generally Authorized or Prohibited destinations
- `get_cfr810_activities` - Get Part 810 activity categories
- `check_cfr810_activity` - Analyze activity for authorization requirements

### Classification Tools
- `suggest_classification` - AI-assisted ECCN/USML suggestions based on item description
- `classification_decision_tree` - Step-by-step classification guidance
- `check_license_exception` - Evaluate applicable license exceptions (TMP, LVS, GOV, etc.)
- `get_recent_updates` - Recent BIS/DDTC Federal Register notices (live API)

### Reference Tools
- `get_country_group_info` - EAR country group membership (A:1, D:1, etc.)
- `get_license_exception_info` - License exception details (LVS, TMP, GOV, ENC, etc.)
- `explain_export_term` - Export control glossary lookup

## Installation

```bash
# Clone the repository
git clone https://github.com/michaelalber/export-assist-mcp.git
cd export-assist-mcp

# Install dependencies
uv sync
```

## Data Ingestion

Download and ingest official government data:

```bash
# Ingest everything (regulations + CSL)
uv run python scripts/ingest_all.py --all

# Regulations only (from eCFR)
uv run python scripts/ingest_all.py --regulations

# Consolidated Screening List (13 combined lists)
uv run python scripts/ingest_all.py --sanctions

# Individual sources
uv run python scripts/ingest_all.py --ear           # EAR only
uv run python scripts/ingest_all.py --itar          # ITAR only

# Load sample data for testing
uv run python scripts/ingest_all.py --sample
```

### Data Sources

| Source | URL | Format |
|--------|-----|--------|
| EAR | https://www.ecfr.gov (15 CFR 730-774) | XML |
| ITAR | https://www.ecfr.gov (22 CFR 120-130) | XML |
| CSL | https://data.trade.gov (primary) | JSON |
| CSL | https://data.opensanctions.org (fallback mirror) | JSON |
| Federal Register | https://www.federalregister.gov/api/v1 | JSON API |

The Consolidated Screening List (CSL) combines 13 government screening lists from Commerce (Entity List, Denied Persons, Unverified List, MEU List), State (ITAR Debarred, Nonproliferation), and Treasury (SDN, FSE, SSI, CAPTA, NS-MBS, NS-CMIC, NS-PLC).

## Usage

### Claude Desktop

Add to your Claude Desktop configuration (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "export-control": {
      "command": "uv",
      "args": ["run", "python", "-m", "export_control_mcp.server"],
      "cwd": "/path/to/export-assist-mcp"
    }
  }
}
```

### Streamable HTTP Transport (Web Integration)

```bash
uv run python -m export_control_mcp.server --transport streamable-http --port 8000
```

Connect to `http://localhost:8000/mcp` for MCP clients.

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=export_control_mcp

# Linting
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Run MCP server (stdio mode)
uv run python -m export_control_mcp.server
```

## Architecture

```
src/export_control_mcp/
├── server.py                 # FastMCP entry point
├── config.py                 # Settings (pydantic-settings)
├── audit.py                  # JSONL audit logging
├── models/                   # Pydantic models
│   ├── regulations.py        # ECCN, RegulationChunk
│   ├── sanctions.py          # EntityListEntry, SDNEntry
│   └── classification.py     # ClassificationSuggestion
├── services/                 # Backend services
│   ├── embeddings.py         # sentence-transformers
│   ├── vector_store.py       # ChromaDB (regulations)
│   ├── sanctions_db.py       # SQLite + FTS5 (sanctions + CSL)
│   └── federal_register.py   # Federal Register API
├── resources/                # Reference data
│   ├── reference_data.py     # Country groups, ECCN/USML, glossary
│   └── doe_nuclear.py        # 10 CFR 810 country lists
├── tools/                    # MCP tools
│   ├── regulations.py        # EAR/ITAR search
│   ├── sanctions.py          # CSL screening
│   ├── classification.py     # Classification assistance
│   └── doe_nuclear.py        # 10 CFR 810 tools
├── rag/                      # RAG components
│   └── chunking.py           # Regulation chunking
└── data/ingest/              # Data ingestion
    ├── ecfr_ingest.py        # eCFR regulations
    ├── sanctions_ingest.py   # Legacy OFAC/BIS lists
    └── csl_ingest.py         # Consolidated Screening List
```

## Environment Variables

```bash
# Storage
EXPORT_CONTROL_CHROMA_PERSIST_DIR=./data/chroma
EXPORT_CONTROL_SANCTIONS_DB_PATH=./data/sanctions.db

# Embeddings
EXPORT_CONTROL_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Logging
EXPORT_CONTROL_LOG_LEVEL=INFO
EXPORT_CONTROL_AUDIT_LOG_PATH=./logs/audit.jsonl

# Transport
EXPORT_CONTROL_MCP_TRANSPORT=stdio
```

## Security Notes

- All data processing is local (embeddings, vector store, SQLite)
- Audit logging captures all tool invocations
- No external API calls except for data ingestion from official government sources
- Suitable for CUI-adjacent environments (consult ISSM for classified networks)

## Author

Michael K Alber

## License

Apache-2.0 - 2026 Michael K Alber
