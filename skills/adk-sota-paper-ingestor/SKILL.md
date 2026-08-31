---
name: adk-sota-paper-ingestor
description: Automated SOTA Research & Auto-Implementation Workflow for ADK. Discovers breakthrough papers, immediately writes dossiers in scientific_papers/, proposes code implementation to user, and upon approval implements functional code and synchronizes ALL system documentation.
---

# ADK SOTA Paper & Code Auto-Implementation Skill

This skill defines the standardized 4-step procedural workflow for searching, recording, proposing, implementing, and documenting breakthrough SOTA research (2023–2026) in the `Artificial-Degree-Printer` framework.

---

## 🛑 STRICT RULE: ZERO EMPTY / ZERO-BYTE FILES GUARANTEE

> **NEVER CREATE OR LEAVE EMPTY (0-BYTE) FILES IN DOCUMENTATION OR CODE.**  
> Every created paper dossier, documentation file, or code file MUST contain complete, rich, structured analytical markdown (headings, citation keys, arXiv/DOI links, theoretical findings, implementation items, and strengths).  
> Creating placeholders or empty files is strictly forbidden.

---

## 📋 The 4-Step Autonomous Workflow Protocol

```
  [ STEP 1: DISCOVER & RECORD DOSSIER ] -> Search 2023-2026 paper, create full dossier in scientific_papers/, update index
                     │
                     ▼
  [ STEP 2: PROPOSE CODE IMPLEMENTATION ] -> Present breakthrough & ask for approval ("Czy wdrażamy w kodzie?")
                     │
                     ▼ (Upon User Approval)
  [ STEP 3: CODE & TEST ]               -> Implement functional engine in adk/ & unit tests in tests/
                     │
                     ▼
  [ STEP 4: DOCS & BUILD LOG ]          -> Synchronize ALL core documentation files & append sequential Etap
```

---

## 🛠️ Detailed Step Execution Protocol

### Step 1: Discover, Analyze & Record Dossier (Immediate Persistence)
1. Search arXiv / top-tier venues for breakthrough SOTA papers ($\ge 2023$, $\le 3$ years horizon).
2. Evaluate fit against ADK's core mission (IT app generation + 40–80 page thesis co-synthesis).
3. **Immediately write the complete analytical dossier** in `documentation/scientific_papers/<citation_key>.md` with rich markdown content.
4. Update `documentation/scientific_papers/README.md`, `master_implementation_synthesis.md`, and `search_keywords_taxonomy.md`.

### Step 2: Propose Code Implementation to User (Approval Gate)
1. Present a concise, high-impact summary of the breakthrough to the user.
2. State clearly that the paper has already been analyzed and saved in `scientific_papers/`.
3. **Ask for explicit user approval to implement the code & system architecture** (*"Karta pliku została zapisana w bazie. Czy wdrażamy te rozwiązania bezpośrednio w kodzie i głównej dokumentacji projektu?"*).

### Step 3: Implement Code & Tests
Upon user approval ("tak"):
1. Implement functional code modifications in `adk/engine/`, `adk/tools/`, `adk/llm/`, or `adk/verification/`.
2. Write automated unit/integration tests in `tests/`.
3. Run `python -m pytest tests/ -v` and verify **100% PASS**.

### Step 4: Synchronize ALL Core System Documentation
1. Update ALL core system documentation (`architecture.md`, `methodology_and_roadmap.md`, `workflow.md`, `requirements.md`, `repository-structure.md`, `project-overview.md`).
2. Append sequential, unbroken build stage (Etap 1, 2, ..., N) to `documentation/build_log_and_changelog.md`.
