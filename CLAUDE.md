# Export Control MCP Server

## Project Overview

A FastMCP-based Model Context Protocol server providing AI assistant capabilities for National Laboratory Export Control groups. Enables querying of regulations (EAR/ITAR), sanctions lists, commodity classifications, and compliance guidance.

**Key design decisions:**
- **Local-first**: Embeddings and vector store run locally. No data leaves the network.
- **Tool-based architecture**: Each export control function is a discrete MCP tool with clear contracts. Enables granular permissions and audit logging.
- **Async throughout**: FastMCP is async-native. All I/O uses async patterns.
- **Structured outputs**: Tools return Pydantic models. Let the LLM format for the user.
- **Audit-ready**: Every tool invocation logs timestamp, tool name, sanitized parameters, and result summary.

## Tech Stack

| Component | Choice |
|-----------|--------|
| MCP Framework | FastMCP (>=0.4.0) |
| Vector Store | ChromaDB (embedded, no external service) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Data Models | Pydantic 2.0+ |
| Config | pydantic-settings (EXPORT_CONTROL_* env vars) |
| HTTP Client | httpx (async) |
| Document Processing | pypdf, docling, openpyxl, lxml, defusedxml |
| Fuzzy Matching | rapidfuzz (sanctions screening) |
| Token Counting | tiktoken (chunking) |
| Testing | pytest, pytest-asyncio, pytest-cov |
| Linting | Ruff (linting + formatting) |
| Type Checking | mypy (strict) |
| Security | bandit |

## Architecture

```
src/export_control_mcp/
├── __init__.py
├── server.py              # FastMCP server entry point
├── config.py              # Settings via pydantic-settings
├── audit.py               # JSONL audit logging
├── models/
│   ├── errors.py          # Custom exceptions
│   ├── regulations.py     # RegulationChunk, ECCN, USML
│   ├── sanctions.py       # EntityListEntry, SDNEntry
│   └── classification.py  # ClassificationSuggestion
├── services/
│   ├── embeddings.py      # sentence-transformers wrapper
│   ├── vector_store.py    # ChromaDB operations
│   ├── sanctions_db.py    # SQLite + FTS5 for CSL/sanctions
│   └── federal_register.py # Federal Register API client
├── tools/
│   ├── regulations.py     # EAR/ITAR semantic search
│   ├── sanctions.py       # CSL screening tools
│   ├── classification.py  # ECCN/USML assistance
│   └── doe_nuclear.py     # 10 CFR 810 nuclear controls
├── resources/
│   ├── reference_data.py  # Country groups, glossary
│   ├── country_sanctions.py # Country sanctions summary
│   └── doe_nuclear.py     # 10 CFR 810 country lists
├── rag/
│   └── chunking.py        # Document chunking strategies
└── data/ingest/
    ├── base.py            # Base ingestor class
    ├── ecfr_ingest.py     # eCFR XML regulation ingestion
    ├── ear_ingest.py      # EAR-specific ingestion
    ├── sanctions_ingest.py # Legacy OFAC/BIS lists
    └── csl_ingest.py      # Consolidated Screening List
```

## Commands

```bash
# Setup
pip install -e ".[dev]"

# Run server (stdio - default for Claude Desktop)
export-control-mcp

# Run server (HTTP)
EXPORT_CONTROL_MCP_TRANSPORT=streamable-http export-control-mcp

# Test
pytest
pytest --cov=src/export_control_mcp --cov-report=term-missing

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
mypy src/

# Security scan
bandit -r src/ -c pyproject.toml

# Data ingestion
python scripts/ingest_all.py --all
python scripts/ingest_regulations.py
python scripts/update_sanctions.py

# Docker
docker compose up -d
docker compose logs -f
docker compose down
```

## Development Principles

### TDD is Mandatory
1. **Never write production code without a failing test first**
2. Cycle: RED (write failing test) → GREEN (minimal code to pass) → REFACTOR
3. Run tests before committing: `pytest`
4. Coverage target: 80% minimum for business logic, 95% for security-critical code

### Security by Design (OWASP)
- Validate all inputs at system boundaries
- Use defusedxml for all XML parsing (prevents XXE attacks)
- Sanitize filenames and user-provided paths
- Follow OWASP guidelines for data protection

### YAGNI (You Aren't Gonna Need It)
- No abstract interfaces until needed (Rule of Three)
- No dependency injection containers
- Prefer composition over inheritance
- Add abstractions only when patterns emerge

## Code Standards

- Type hints on all signatures
- Google-style docstrings for public methods
- Arrange-Act-Assert test pattern
- `pathlib.Path` over string paths
- Specific exceptions, never bare `except:`
- Async for I/O-bound operations
- Pydantic models for all data structures

## Quality Gates

- **Cyclomatic Complexity**: Methods <10, classes <20
- **Code Coverage**: 80% minimum for business logic, 95% for security-critical code
- **Maintainability Index**: Target 70+
- **Code Duplication**: Maximum 3%

## Git Workflow

- Commit after each GREEN phase
- Commit message format: `feat|fix|test|refactor: brief description`
- Don't commit failing tests (RED phase is local only)

## Testing Patterns

```python
# Arrange-Act-Assert pattern
@pytest.mark.asyncio
async def test_search_ear_returns_results():
    # Arrange
    service = RegulationSearchService()

    # Act
    results = await service.search("encryption", regulation_type="EAR", limit=5)

    # Assert
    assert len(results) > 0
    assert results[0].regulation_type == "EAR"
```

### Test Categories

- `tests/test_tools/` - Tool implementation tests
- `tests/test_services/` - Service layer tests
- `tests/test_data_ingest/` - Ingestion pipeline tests
- `tests/test_data_validation/` - Reference data validation
- `tests/test_rag/` - RAG/chunking tests
- `tests/test_integration/` - Full MCP protocol tests

## MCP Tools

### Regulations Tools
- `search_ear` - Search Export Administration Regulations
- `search_itar` - Search ITAR (22 CFR 120-130)
- `get_eccn` - Lookup specific ECCN details
- `get_usml_category` - Lookup USML category details
- `compare_jurisdictions` - EAR vs ITAR jurisdiction analysis

### Sanctions Tools
- `search_entity_list` - BIS Entity List search
- `search_sdn_list` - OFAC SDN List search
- `check_country_sanctions` - Country-specific sanctions summary
- `search_denied_persons` - Denied Persons List search

### Classification Tools
- `suggest_classification` - Given item description, suggest ECCN/USML
- `classification_decision_tree` - Walk through classification logic
- `check_license_exception` - Evaluate applicable license exceptions

### Reference Tools
- `get_country_group` - Return country group membership (A:1, D:1, etc.)
- `get_recent_updates` - Recent BIS/DDTC Federal Register notices
- `explain_term` - Export control glossary lookup

### Data Sources
- **EAR**: https://www.ecfr.gov (15 CFR 730-774) — XML
- **ITAR**: https://www.ecfr.gov (22 CFR 120-130) — XML
- **CSL**: https://data.trade.gov — JSON (primary), https://data.opensanctions.org — JSON (fallback)
- **Federal Register**: https://www.federalregister.gov/api/v1 — JSON API

## Environment Variables

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

## Integration Points

### Claude Desktop (Local)
```json
{
  "mcpServers": {
    "export-control": {
      "command": "export-control-mcp"
    }
  }
}
```

### .NET Application (Production)
- Connect via Streamable HTTP transport to `http://localhost:8000/mcp`
- Use MCP C# SDK or HTTP client with streaming support
- Pass user context in MCP request metadata for audit logging

## Security Considerations

- This server handles CUI-adjacent data. Do not deploy on classified networks without ISSM approval.
- Audit logging is mandatory for production use.
- Vector store contains regulation text only—no internal project data without explicit scoping.
- All external API calls (sanctions list updates) must go through approved proxy if on lab network.

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [BIS Export Administration Regulations](https://www.bis.doc.gov/ear)
- [DDTC ITAR](https://www.pmddtc.state.gov/ddtc_public/ddtc_public?id=ddtc_public_portal_itar_landing)
- [OFAC Sanctions Lists](https://ofac.treasury.gov/sanctions-list-service)
