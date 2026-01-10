# Export Control MCP Server

## Project Overview

A FastMCP-based Model Context Protocol server providing AI assistant capabilities for National Laboratory Export Control groups. Enables querying of regulations (EAR/ITAR), sanctions lists, commodity classifications, and internal tracking systems.

## Tech Stack

- **Runtime**: Python 3.11+
- **Framework**: FastMCP (MCP SDK)
- **Vector Store**: ChromaDB (local, no external dependencies)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2 for efficiency, or BGE for quality)
- **Document Processing**: pypdf, python-docx, unstructured
- **HTTP Client**: httpx (async)
- **Testing**: pytest, pytest-asyncio

## Architecture

```
src/
├── export_control_mcp/
│   ├── __init__.py
│   ├── server.py           # FastMCP server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── regulations.py  # EAR/ITAR/CCL search tools
│   │   ├── sanctions.py    # OFAC/Entity List queries
│   │   ├── classification.py # ECCN/USML lookup
│   │   └── internal.py     # Internal DB queries (stub for now)
│   ├── resources/
│   │   ├── __init__.py
│   │   └── reference_docs.py # Static reference materials
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py   # Embedding generation
│   │   ├── vectorstore.py  # ChromaDB operations
│   │   └── chunking.py     # Document chunking strategies
│   └── config.py           # Settings via pydantic-settings
├── scripts/
│   ├── ingest_regulations.py  # Load EAR/ITAR PDFs into vector store
│   └── update_sanctions.py    # Fetch latest OFAC/BIS lists
├── data/
│   ├── regulations/        # PDF/HTML source documents
│   ├── sanctions/          # Downloaded lists
│   └── chroma/             # Vector store persistence
└── tests/
    ├── conftest.py
    ├── test_tools/
    └── test_rag/
```

## Key Design Decisions

1. **Local-first**: All inference-adjacent operations (embeddings, vector store) run locally. No data leaves the network unless explicitly configured for external LLM APIs.

2. **Tool-based architecture**: Each export control function is a discrete MCP tool with clear input/output contracts. Enables granular permissions and audit logging.

3. **Async throughout**: FastMCP is async-native. All I/O operations use async patterns for responsiveness.

4. **Structured outputs**: Tools return structured data (Pydantic models) rather than raw text where possible. Let the LLM format for the user.

5. **Audit-ready**: Every tool invocation logs: timestamp, tool name, parameters (sanitized), user context (if available), result summary.

## MCP Tools to Implement

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

## Environment Variables

```bash
# Required
CHROMA_PERSIST_DIR=./data/chroma

# Optional - for external LLM (if not using local)
OPENAI_API_KEY=           # If using OpenAI embeddings
ANTHROPIC_API_KEY=        # If calling Claude from tools

# Logging
LOG_LEVEL=INFO
AUDIT_LOG_PATH=./logs/audit.jsonl
```

## Development Commands

```bash
# Install dependencies
uv sync

# Run MCP server (stdio mode for Claude Desktop)
uv run python -m export_control_mcp.server

# Run with SSE for web integration
uv run python -m export_control_mcp.server --transport sse --port 8000

# Ingest regulations
uv run python scripts/ingest_regulations.py --source ./data/regulations/

# Update sanctions lists
uv run python scripts/update_sanctions.py

# Run tests
uv run pytest

# Type checking
uv run mypy src/
```

## Security Considerations

- This server handles CUI-adjacent data. Do not deploy on classified networks without ISSM approval.
- Audit logging is mandatory for production use.
- Vector store contains regulation text only—no internal project data without explicit scoping.
- All external API calls (sanctions list updates) must go through approved proxy if on lab network.

## Integration Points

### Claude Desktop (Local Development)
```json
{
  "mcpServers": {
    "export-control": {
      "command": "uv",
      "args": ["run", "python", "-m", "export_control_mcp.server"],
      "cwd": "/path/to/export-control-mcp"
    }
  }
}
```

### .NET Application (Production)
- Connect via SSE transport to `http://localhost:8000/sse`
- Use MCP C# SDK or raw HTTP/SSE client
- Pass user context in MCP request metadata for audit logging

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [BIS Export Administration Regulations](https://www.bis.doc.gov/ear)
- [DDTC ITAR](https://www.pmddtc.state.gov/ddtc_public/ddtc_public?id=ddtc_public_portal_itar_landing)
- [OFAC Sanctions Lists](https://ofac.treasury.gov/sanctions-list-service)
