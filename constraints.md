# export-control-mcp — Constraints

---

## Must Do

- Load and confirm context (AGENTS.md, intent.md, constraints.md) before every session.
- Write a failing test before writing any production code — TDD is mandatory, no exceptions.
- Preserve audit logging on every code path that invokes an MCP tool; do not remove or short-circuit it.
- Use `defusedxml` for all XML parsing of external or untrusted data.
- Sanitize audit log parameters — redact passwords, tokens, API keys, and PII before logging.
- Run the full CI gate (`pytest`, `ruff check src/ tests/`, `mypy src/`, `bandit -r src/ -c pyproject.toml`) before declaring any task done.
- Confirm with Michael before executing any irreversible action (delete, force-push, schema change).
- Add a `# VERIFY:` comment rather than guess when uncertain about a function signature or API behavior.

---

## Must NOT Do

- Do not change a tool's MCP contract (name, parameters, return type) without explicit approval.
- Do not hardcode secrets, API keys, or credentials — use `EXPORT_CONTROL_*` environment variables only.
- Do not commit `.env` files, build artifacts, ChromaDB data, or generated SQLite databases.
- Do not bind HTTP transport to `0.0.0.0` — always `127.0.0.1`.
- Do not log CUI-adjacent content (sanctions records, classification details) beyond the required audit schema fields.
- Do not add a new runtime dependency without running `pip-audit` and pinning the version in `pyproject.toml`.
- Do not re-litigate decisions already logged in AGENTS.md Persistent Decisions.
- Do not exceed task scope without explicit approval from Michael.

---

## Preferences

- Prefer editing existing files over creating new ones.
- Prefer `pathlib.Path` over `os.path` for all file operations.
- Prefer `async def` / `asyncio` for I/O-bound work — match existing async patterns throughout.
- Prefer the grounded-code-mcp `python` collection over training data for FastMCP, Pydantic, and pytest idioms.
- Prefer specific exception types over bare `except:` — always catch the narrowest applicable type.
- Prefer flagging a problem before executing a workaround.
- Prefer brevity over completeness unless depth is explicitly requested.

---

## Escalate Rather Than Decide

- Any change to a tool's public MCP contract.
- Any change to ingestion logic that could affect regulation or sanctions data accuracy.
- Any new external data source or API integration.
- Any security-relevant decision not explicitly covered by these constraints.
- Any request where the fix would require modifying more than one tool's contract simultaneously.

---

## Code Quality Gates

- **Test coverage (business logic):** ≥ 80% — `pytest --cov=src/export_control_mcp --cov-report=term-missing`
- **Test coverage (security-critical paths — audit logging, input validation):** ≥ 95%
- **Cyclomatic complexity (per method):** < 10
- **Code duplication:** ≤ 3%
- **Commit format:** Conventional Commits — `feat:`, `fix:`, `refactor:`, `chore:`, `test:`, `docs:`
- **Commit scope:** Atomic — one logical change per commit; no bundling unrelated changes
- **Lint:** `ruff check src/ tests/` — zero errors
- **Type check:** `mypy src/` — zero errors (strict mode)
- **Security:** `bandit -r src/ -c pyproject.toml` — zero high or critical issues
- **Dependency audit:** `pip-audit` — zero unfixed high or critical CVEs
