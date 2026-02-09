# Export Control MCP Server

[![CI](https://github.com/michaelalber/export-assist-mcp/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/michaelalber/export-assist-mcp/actions/workflows/ci.yml)
[![Security](https://github.com/michaelalber/export-assist-mcp/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/michaelalber/export-assist-mcp/actions/workflows/security.yml)

MCP server providing AI assistant tools for export control compliance (EAR/ITAR/OFAC). Designed for National Laboratory Export Control groups.

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

### DOE Nuclear Tools (10 CFR 810)
- `check_cfr810_country` - Check nuclear technology transfer authorization status
- `list_cfr810_countries` - List Generally Authorized or Prohibited destinations
- `get_cfr810_activities` - Get Part 810 activity categories
- `check_cfr810_activity` - Analyze activity for authorization requirements

### Classification Tools
- `suggest_classification` - AI-assisted ECCN/USML suggestions
- `classification_decision_tree` - Step-by-step classification guidance
- `check_license_exception` - Evaluate applicable license exceptions
- `get_recent_updates` - Recent BIS/DDTC Federal Register notices (live API)

### Reference Tools
- `get_country_group_info` - EAR country group membership (A:1, D:1, etc.)
- `get_license_exception_info` - License exception details
- `explain_export_term` - Export control glossary lookup

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install
pip install -e .

# Ingest data (regulations + sanctions)
python scripts/ingest_all.py --all

# Run server (stdio transport)
export-control-mcp

# Run server (HTTP transport)
EXPORT_CONTROL_MCP_TRANSPORT=streamable-http export-control-mcp
```

### Using Docker

```bash
docker compose up -d
```

The server will be available at `http://localhost:8000`.

## Data Sources

| Source | URL | Format |
|--------|-----|--------|
| EAR | https://www.ecfr.gov (15 CFR 730-774) | XML |
| ITAR | https://www.ecfr.gov (22 CFR 120-130) | XML |
| CSL | https://data.trade.gov (primary) | JSON |
| CSL | https://data.opensanctions.org (fallback) | JSON |
| Federal Register | https://www.federalregister.gov/api/v1 | JSON API |

## Configuration

Environment variables (prefix: `EXPORT_CONTROL_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPORT_CONTROL_MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `EXPORT_CONTROL_MCP_HOST` | `127.0.0.1` | HTTP server host |
| `EXPORT_CONTROL_MCP_PORT` | `8000` | HTTP server port |
| `EXPORT_CONTROL_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `EXPORT_CONTROL_CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage |
| `EXPORT_CONTROL_SANCTIONS_DB_PATH` | `./data/sanctions.db` | Sanctions SQLite DB |
| `EXPORT_CONTROL_LOG_LEVEL` | `INFO` | Logging level |
| `EXPORT_CONTROL_AUDIT_LOG_PATH` | `./logs/audit.jsonl` | Audit log location |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

See [CLAUDE.md](CLAUDE.md) for architecture documentation.

## Security Notes

- All data processing is local (embeddings, vector store, SQLite)
- Audit logging captures all tool invocations
- No external API calls except for data ingestion from official government sources
- Suitable for CUI-adjacent environments (consult ISSM for classified networks)

## Author

Michael K Alber ([@michaelalber](https://github.com/michaelalber))

## License

Apache License 2.0 - see [LICENSE](LICENSE)
