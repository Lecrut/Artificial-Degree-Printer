---
name: adk-typst-template-tester
description: Validates and tests Typst 0.11+ and LaTeX academic thesis template compilation, verifying BibTeX citations, SVG charts, CeTZ vector diagrams, and dual-engine export capabilities. Use when modifying or testing thesis output templates.
---

# ADK Typst & LaTeX Template Tester Skill

This skill defines the verification protocol for testing academic typesetting templates (`adk/templates/typst/` and `adk/templates/latex/`).

---

## 📋 Activation Criteria
Trigger this skill whenever modifying `thesis.typ`, `thesis.tex`, `references.bib`, or `TypesettingTool` export logic.

---

## 🛠️ Step-by-Step Execution Protocol

### Step 1: Typst 0.11+ Syntax Check
1. Inspect `adk/templates/typst/thesis.typ`.
2. Verify template layout parameters:
   - Margins: 2.5 cm on all sides.
   - Line spacing: 1.5.
   - Font: Times New Roman or Liberation Serif (academic standard).
   - Bibliography: `#bibliography("references.bib", style: "ieee")`.
3. Check for CeTZ package imports for vector diagrams (`#import "@preview/cetz:0.2.2"`).

### Step 2: LaTeX Dual-Export Parity Check
1. Inspect `adk/templates/latex/thesis.tex`.
2. Verify syntax compatibility with Overleaf / `pdflatex` / `biber`.
3. Check that structural headers (`\chapter{}`, `\section{}`) map 1:1 with Typst headings (`= Heading`, `== Subheading`).

### Step 3: Run Typesetting Tool Verification
Execute the typesetting tool test:
```bash
python -m pytest tests/test_tools.py -k test_typesetting_tool_export -v
```
Verify that:
- Plik `artifacts/thesis/thesis.typ` i `artifacts/thesis/thesis.tex` zostają wygenerowane.
- Wskazany plik BibTeX jest tworzony i zawiera unikalne klucze cytowań.
- Brak błędów kompilacji podczas generowania eksportu.

