# export-control-mcp — Intent

---

## Agent Architecture

**This project uses:** Coding harness

**Reason:** Single-developer maintenance project; Michael reviews every output before merge. No autonomous multi-session execution required.

---

## Primary Goal

Keep the export-control-mcp server accurate, stable, and secure — regulation and sanctions data current, tool contracts unchanged, security posture clean — so National Lab export control staff can trust its guidance without manual verification of every response.

---

## Values (What We Optimize For)

1. **Correctness** — wrong export control guidance has legal and compliance consequences
2. **Security** — CUI-adjacent data; mandatory audit logging; no data exfiltration
3. **Maintainability** — solo-maintained; code must be legible months after it was written
4. **Performance** — acceptable local response times; no SLA, but no unnecessary latency
5. **Speed of delivery** — never sacrificed for correctness

---

## Tradeoff Rules

| Conflict | Resolution |
|---|---|
| Speed vs. correctness | Always correctness. Export control errors carry legal risk. |
| Completeness vs. brevity | Prefer brevity unless depth is explicitly requested. |
| New feature vs. stability | Maintenance phase: prefer stability. New features require explicit approval. |
| Upstream change vs. backward compatibility | Update tool contract and tests together; never silently swallow an API change. |

---

## Decision Boundaries

### Decide Autonomously

- Formatting, naming, import ordering within established conventions
- Tool selection for read-only exploration
- Refactoring within an approved, scoped task (while keeping all tests green)
- Choosing between equivalent implementations when both pass tests, lint, and type-check

### Escalate to Human

- Any change to a tool's MCP contract (name, parameters, return shape) — downstream clients may break
- Any change to ingestion logic that affects regulation or sanctions data accuracy
- Any new external dependency or data source
- Any security-relevant decision not explicitly covered by `constraints.md`
- Any scope change beyond the stated task

---

## What "Good" Looks Like

A good output for this project:

- Passes all CI gates (`pytest`, `ruff check`, `mypy src/`, `bandit`) without new warnings
- Does not change a tool's public MCP contract without explicit approval
- Audit logging is present on every modified tool invocation path
- `defusedxml` is used for any new XML parsing; never bare `lxml` on untrusted input
- Changes are atomic and committable with a single Conventional Commits message

---

## Anti-Patterns (What Bad Looks Like)

- Silently changing a tool's return shape without updating tests and flagging the contract change
- Removing or bypassing audit logging to simplify code
- Adding a new dependency without running `pip-audit` and pinning the version
- Writing production code before a failing test exists
- Treating a passing CI run as "the output is correct" — CI verifies code; Michael verifies guidance accuracy

---

## Persistent Decisions

| Date | Decision | Rationale |
|---|---|---|
| See AGENTS.md | (Persistent decisions are logged in AGENTS.md) | Single source of truth |

---

## Open Loops

- [ ] [VERIFY: Any outstanding tool contract changes or deprecations planned?]
