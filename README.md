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
- `get_eccn` - Lookup specific ECCN details and control reasons
- `get_usml_category` - Lookup USML category details
- `compare_jurisdictions` - EAR vs ITAR jurisdiction analysis

### Sanctions Tools
- `search_entity_list` - BIS Entity List search with fuzzy name matching
- `search_sdn_list` - OFAC SDN List search
- `search_denied_persons` - BIS Denied Persons List search
- `check_country_sanctions` - Country-specific sanctions summary

### Classification Tools
- `suggest_classification` - AI-assisted ECCN/USML suggestions based on item description
- `classification_decision_tree` - Step-by-step classification guidance
- `check_license_exception` - Evaluate applicable license exceptions (TMP, LVS, GOV, etc.)

### Reference Tools
- `get_country_group` - EAR country group membership (A:1, D:1, etc.)
- `get_recent_updates` - Recent BIS/DDTC Federal Register notices (live API)
- `explain_term` - Export control glossary lookup

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
# Ingest everything (regulations + sanctions)
uv run python scripts/ingest_all.py --all

# Regulations only (from eCFR)
uv run python scripts/ingest_all.py --regulations

# Sanctions lists only
uv run python scripts/ingest_all.py --sanctions

# Individual sources
uv run python scripts/ingest_all.py --ear           # EAR only
uv run python scripts/ingest_all.py --itar          # ITAR only
uv run python scripts/ingest_all.py --sdn           # OFAC SDN only
uv run python scripts/ingest_all.py --denied        # BIS Denied Persons only

# BIS Entity List (requires manual download)
uv run python scripts/ingest_all.py --entity-list /path/to/entity_list.xlsx

# Load sample data for testing
uv run python scripts/ingest_all.py --sample
```

### Data Sources

| Source | URL | Format |
|--------|-----|--------|
| EAR | https://www.ecfr.gov (15 CFR 730-774) | XML |
| ITAR | https://www.ecfr.gov (22 CFR 120-130) | XML |
| OFAC SDN | https://www.treasury.gov/ofac/downloads/sdn.xml | XML |
| BIS Denied Persons | https://www.bis.doc.gov/dpl/dpl.txt | TXT |
| Federal Register | https://www.federalregister.gov/api/v1 | JSON API |

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

### SSE Transport (Web Integration)

```bash
uv run python -m export_control_mcp.server --transport sse --port 8000
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=export_control_mcp

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
│   ├── sanctions_db.py       # SQLite + FTS5 (sanctions)
│   └── federal_register.py   # Federal Register API
├── tools/                    # MCP tools
│   ├── regulations.py        # EAR/ITAR search
│   ├── sanctions.py          # Sanctions screening
│   └── classification.py     # Classification assistance
├── rag/                      # RAG components
│   └── chunking.py           # Regulation chunking
└── data/ingest/              # Data ingestion
    ├── ecfr_ingest.py        # eCFR regulations
    └── sanctions_ingest.py   # OFAC/BIS lists
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

## License

Apache-2.0
