# export-control-mcp — Evals

---

## Eval Philosophy

Evals are safety infrastructure — write them before the agent starts. A passing CI run verifies code correctness; evals verify the tool outputs are actually accurate relative to export control law. A passing eval would survive scrutiny from an export control officer reviewing the guidance.

---

## Test Cases

### Test Case 1: Regulation Search

- **Input / Prompt:** Call `search_ear` with query `"encryption"`, limit 5
- **Known-Good Output:** ≥1 result; each has `regulation_type == "EAR"`, non-empty `text`, and a valid CFR citation or ECCN reference
- **Pass Criteria:**
  - [ ] `pytest tests/test_tools/test_regulations.py` — all pass
  - [ ] Results reference 15 CFR 742.15 or EAR encryption controls
  - [ ] No `regulation_type == "ITAR"` results returned from `search_ear`
- **Last Run:** [VERIFY: date] | **Result:** [VERIFY]
- **Notes:**

---

### Test Case 2: Sanctions Screening

- **Input / Prompt:** Call `search_consolidated_screening_list` with a known publicly-listed SDN entity name
- **Known-Good Output:** Returns a match with correct source list attribution and confidence ≥ 0.8; clearly non-matching names return no results
- **Pass Criteria:**
  - [ ] `pytest tests/test_tools/test_sanctions.py` — all pass
  - [ ] Known entity is found with calibrated confidence score
  - [ ] No false positives on clearly non-matching control names
- **Last Run:** [VERIFY: date] | **Result:** [VERIFY]
- **Notes:**

---

### Test Case 3: Classification Suggestion

- **Input / Prompt:** Call `suggest_classification` with description `"fiber optic gyroscope for navigation"`
- **Known-Good Output:** Suggests USML Category XII or EAR ECCN 7A994/7A004 with reasoning citing specific control parameters (e.g., accuracy thresholds)
- **Pass Criteria:**
  - [ ] `pytest tests/test_tools/test_classification.py` — all pass
  - [ ] Suggestion includes ≥1 plausible ECCN or USML category
  - [ ] Reasoning cites a specific control parameter, not a vague category name
- **Last Run:** [VERIFY: date] | **Result:** [VERIFY]
- **Notes:**

---

### Test Case 4: DOE 10 CFR 810 Nuclear Check

- **Input / Prompt:** Call `check_cfr810_country` for Australia (Generally Authorized) and one Prohibited destination
- **Known-Good Output:** Australia → Generally Authorized; prohibited country → correct status with specific regulatory basis from 10 CFR 810 Appendix A
- **Pass Criteria:**
  - [ ] `pytest tests/test_tools/test_doe_nuclear.py` — all pass
  - [ ] Status values match current 10 CFR 810 Appendix A
  - [ ] No country returns an ambiguous or empty authorization status
- **Last Run:** [VERIFY: date] | **Result:** [VERIFY]
- **Notes:**

---

### Test Case 5: Maintenance Task (Any Code Change)

- **Input / Prompt:** Any change to an existing tool or service
- **Known-Good Output:** All existing tests pass; no new ruff/mypy/bandit violations; audit log entries are present on every modified tool invocation path
- **Pass Criteria:**
  - [ ] `pytest` — all pass, no regressions
  - [ ] `ruff check src/ tests/` — clean
  - [ ] `mypy src/` — clean (strict)
  - [ ] `bandit -r src/ -c pyproject.toml` — zero high/critical
  - [ ] MCP tool contract unchanged, or change was explicitly approved by Michael
- **Last Run:** | **Result:**
- **Notes:**

---

## Taste Rules (Encoded Rejections)

| # | Pattern to Reject | Why It Fails | Rule |
|---|---|---|---|
| 1 | Output that looks right but isn't grounded in project context | Generic output requires cleanup and defeats delegation | Anchor every recommendation to a specific fact from AGENTS.md or the active task |
| 2 | Tool implementation that omits audit logging | Breaks the mandatory audit trail | Every tool invocation path must call the audit logger |
| 3 | XML parsing with bare `lxml` on external data | XXE vulnerability | Always use `defusedxml` for untrusted XML |
| 4 | Changing a tool return type without updating tests | Silent contract break; downstream clients break silently | Tool contract changes require simultaneous test updates and explicit approval |

---

## CI Gate

- **Lint:** `ruff check src/ tests/` — zero errors
- **Format:** `ruff format --check src/ tests/` — clean
- **Type check:** `mypy src/` — zero errors
- **Tests:** `pytest` — all pass (CI matrix: Python 3.10, 3.11, 3.12)
- **Coverage:** ≥ 80% — `pytest --cov=src/export_control_mcp --cov-report=term-missing`
- **Security:** `bandit -r src/ -c pyproject.toml` — zero high or critical
- **Dependency audit:** `pip-audit` — zero unfixed high/critical CVEs

> Append CI gate results as a sub-item of each Test Case entry on every run.

---

## Rejection Log

*(No entries yet — add rejected outputs here as they occur.)*
