---
name: adk-code-quality-auditor
description: Performs rigorous code quality audits for the ADK Python codebase, verifying Pydantic v2 schemas, AST parse integrity, typing compliance, and 100% test pass rates across pytest. Use when adding or refactoring code modules in ADK.
---

# ADK Code Quality Auditor Skill

This skill defines the technical protocol for auditing code quality, model schemas, and execution gates across the `adk/` codebase.

---

## 📋 Activation Criteria
Trigger this skill whenever modifying models in `adk/core/models.py`, adding tools in `adk/tools/`, or refactoring the engine in `adk/engine/`.

---

## 🛠️ Step-by-Step Execution Protocol

### Step 1: Pydantic v2 Schema Audit
1. Inspect modified models in `adk/core/models.py`.
2. Verify all model attributes have explicit `Field(..., description="...")` metadata.
3. Check that default factories use `default_factory=list` or `default_factory=dict` rather than mutable defaults.
4. Verify non-negative / range constraints (e.g. `ge=1900` for year fields).

### Step 2: AST and Module Imports Check
1. Ensure `from __future__ import annotations` is present at the top of Python files.
2. Verify no circular imports exist between `adk/core/`, `adk/engine/`, `adk/tools/`, and `adk/verification/`.
3. Check that type hints use standard Python types (`list[str]`, `dict[str, Any]`, `Optional[...]`).

### Step 3: Run Master Test Suite
Execute the full pytest test suite:
```bash
python -m pytest tests/ -v
```
Verify that:
- 100% of tests pass (`33 passed`).
- Execution time is fast (< 3 seconds).
- No deprecation warnings or unhandled exceptions occur.

### Step 4: Verify Verification Suite Integration
1. Ensure any new model or state field is audited by at least one verification gate in `adk/verification/`.
2. Verify `MasterVerificationSuite` includes the new check and updates `VerificationReport.score`.

