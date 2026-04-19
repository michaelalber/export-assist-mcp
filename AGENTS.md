# export-control-mcp — Project Context

> Project-level context for OpenCode. Supplements your global AGENTS.md — does NOT replace it.
> Global standards (TDD, security rules, quality gates, Python standards, AI behavior) live in the global file.
> This file contains only what is specific to THIS project.

---

## Project Overview

- **Name:** export-control-mcp
- **Purpose:** FastMCP-based MCP server providing AI assistant tools for National Laboratory Export Control groups — querying EAR/ITAR regulations, sanctions lists, commodity classifications, and 10 CFR 810 nuclear controls.
- **Phase:** Maintenance
- **Jira / Confluence:** N/A — single-developer project
- **Definition of success:** Tools return accurate, auditable responses; regulation and sanctions data stays current; no regressions in tool contracts.

---

## Technology Stack

- **Language:** Python 3.10+
- **MCP Framework:** FastMCP ≥0.4.0
- **Vector Store:** ChromaDB (embedded, no external service)
- **Embeddings:** sentence-transformers `all-MiniLM-L6-v2`
- **Data Models / Config:** Pydantic v2, pydantic-settings (`EXPORT_CONTROL_*` env vars)
- **HTTP Client:** httpx (async)
- **Document Processing:** pypdf, docling, openpyxl, lxml, defusedxml
- **Fuzzy Matching:** rapidfuzz (sanctions screening)
- **Token Counting:** tiktoken (chunking)
- **Test Framework:** pytest, pytest-asyncio, pytest-cov
- **Lint / Format:** Ruff (rules: E, W, F, I, N, B, C4, UP, S, T20, SIM, RUF; line length 100)
- **Type Checking:** mypy strict
- **Security Scan:** bandit
- **CI/CD:** GitHub Actions — `.github/workflows/ci.yml` (lint, type-check, test matrix 3.10/3.11/3.12), `.github/workflows/security.yml`
- **Package manager:** pip / uv (`pyproject.toml`, hatchling build backend)

---

## Architecture

- **Pattern:** Feature-slice — capabilities grouped by domain, not by technical layer
- **Entry point:** `src/export_control_mcp/server.py` (FastMCP app + tool/resource registration)
- **Transport:** stdio by default (Claude Desktop); streamable-http on demand (`EXPORT_CONTROL_MCP_TRANSPORT=streamable-http`, host `127.0.0.1:8000`)
- **Key directories:**

```
src/export_control_mcp/
├── server.py              # FastMCP entry point, tool/resource registration
├── config.py              # pydantic-settings; all runtime config via EXPORT_CONTROL_* env vars
├── audit.py               # JSONL audit logging — mandatory on every tool invocation
├── models/
│   ├── errors.py          # Custom exceptions
│   ├── regulations.py     # RegulationChunk, ECCN, USML
│   ├── sanctions.py       # EntityListEntry, SDNEntry
│   └── classification.py  # ClassificationSuggestion
├── services/
│   ├── embeddings.py      # sentence-transformers wrapper
│   ├── vector_store.py    # ChromaDB operations
│   ├── sanctions_db.py    # SQLite + FTS5 for CSL/sanctions (performance-sensitive)
│   └── federal_register.py # Federal Register API client
├── tools/
│   ├── regulations.py     # EAR/ITAR semantic search
│   ├── sanctions.py       # CSL screening tools
│   ├── classification.py  # ECCN/USML assistance
│   └── doe_nuclear.py     # 10 CFR 810 nuclear controls
├── resources/
│   ├── reference_data.py  # Country groups, glossary
│   ├── country_sanctions.py
│   └── doe_nuclear.py     # 10 CFR 810 country lists
├── rag/
│   └── chunking.py        # Document chunking strategies
└── data/ingest/
    ├── base.py            # Base ingestor class
    ├── ecfr_ingest.py     # eCFR XML regulation ingestion
    ├── ear_ingest.py      # EAR-specific ingestion
    ├── sanctions_ingest.py
    └── csl_ingest.py      # CSL — most complex ingestor, dual-source fallback
```

- **Non-obvious constraints:**
  - HTTP transport MUST bind to `127.0.0.1` — never `0.0.0.0`
  - All XML parsing of external/untrusted data MUST use `defusedxml` — never bare `lxml` (XXE prevention)
  - Sanctions screening data and export classifications are CUI-adjacent — sanitize before logging
  - External API calls (Federal Register, CSL) must route through approved proxy on lab networks
  - `asyncio_mode = "auto"` is set — no `@pytest.mark.asyncio` decorator needed on tests

---

## Key Files

| File | Why It Matters |
|---|---|
| `src/export_control_mcp/server.py` | FastMCP app entry point — all tool and resource registration |
| `src/export_control_mcp/config.py` | All runtime configuration; authoritative env var reference |
| `src/export_control_mcp/audit.py` | JSONL audit logger — must be called on every tool invocation path |
| `src/export_control_mcp/tools/regulations.py` | Core regulation search tools; largest tool surface |
| `src/export_control_mcp/services/sanctions_db.py` | SQLite + FTS5 sanctions screening — latency-sensitive |
| `src/export_control_mcp/data/ingest/csl_ingest.py` | Most complex ingestor; dual-source fallback (trade.gov → opensanctions.org) |

---

## MCP Tool Surface

| Tool | Domain |
|---|---|
| `search_ear`, `search_itar`, `search_regulations` | EAR/ITAR regulation search |
| `get_eccn_details`, `get_usml_category_details`, `compare_jurisdictions` | ECCN/USML lookup |
| `search_consolidated_screening_list`, `get_csl_statistics`, `check_country_sanctions` | Sanctions screening |
| `check_cfr810_country`, `list_cfr810_countries`, `get_cfr810_activities`, `check_cfr810_activity` | DOE 10 CFR 810 |
| `suggest_classification`, `classification_decision_tree`, `check_license_exception` | Classification |
| `get_recent_updates` | Federal Register live API |
| `get_country_group_info`, `get_license_exception_info`, `explain_export_term` | Reference |

---

## Persistent Decisions

| Date | Decision | Rationale |
|---|---|---|
| [VERIFY: date] | Local-first: embeddings and vector store run locally | No data leaves the network — required for CUI-adjacent environments |
| [VERIFY: date] | Tool-based architecture: each function is a discrete MCP tool | Enables granular permissions and audit logging per tool invocation |
| [VERIFY: date] | Async throughout | FastMCP is async-native; all I/O uses async patterns |
| [VERIFY: date] | Structured Pydantic outputs | Consistent tool contracts; LLM handles formatting for the user |
| [VERIFY: date] | ChromaDB embedded, no external service | Eliminates infrastructure dependency for local deployments |
| [VERIFY: date] | SQLite + FTS5 for sanctions screening | Low-latency local fuzzy search without an external database |

---

## Open Loops

- [ ] [VERIFY: Any pending CSL/trade.gov API schema changes that affect ingestion?]
- [ ] [VERIFY: Any known failing tool contracts or test gaps to address?]

---

## Team

| Name | Role |
|---|---|
| Michael K. Alber | Sole developer |

---

## Available Tools

- **grounded-code-mcp** — local knowledge base; use `collection="python"` for FastMCP, Pydantic v2, pytest, and httpx idioms

---

## Project Boot Ritual

At the start of every session:

1. Read this file (`AGENTS.md`), `intent.md`, and `constraints.md`.
2. Check `Open Loops` above — surface any unresolved items.
3. Confirm context: phase (Maintenance), active task, top constraints, open loops.
4. Do NOT begin work until context is confirmed.
