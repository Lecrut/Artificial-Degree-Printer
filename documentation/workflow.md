# Execution Workflow & State Transitions (ADK 2027)

> **Workflow Pattern:** Deterministic DAG & Closed-Loop Agentic Reflexion  
> **Standard:** Metodyka ADK-TRACE  
> **Engine:** `StateGraphEngine` (`adk/engine/graph.py`)

---

## 1. The 6-Stage Execution Pipeline

```
  [1. INTAKE]  ────────▶  [2. RESEARCH]  ────────▶  [3. ARCHITECTURE]
  Promotor AI            Researcher Agent           Architect Agent
  (Requirements)         (SOTA >= 2023)             (C4 & Pydantic)
                                                           │
                                                           ▼
  [6. VERIFICATION] ◀───  [5. TYPESETTING]  ◀───  [4. IMPLEMENTATION]
  Master Suite           Typesetter Agent           Developer & Benchmarker
  (7 Quality Gates)      (Typst & LaTeX)            (Pytest, SVG Charts)
```

---

## 2. Detailed Stage Breakdown

### Stage 1: Problem Intake & Requirements Framing
- **Agent:** `OrchestratorAgent` (Promotor AI)
- **Input:** High-level project topic (e.g. *"System analizy wydajnosci mikroserwisow w chmurze"*).
- **Artifacts:** `ThesisMetadata`, `List[Requirement]` with MoSCoW priorities (`MUST`, `SHOULD`, `COULD`).

### Stage 2: SOTA Literature Discovery & Implementation Backlog
- **Agent:** `ResearcherAgent`
- **Tool:** `DynamicLiteratureSearchEngine` + `LiteratureDossierTool`
- **Action:** Dynamically searches seminal papers published in **2023–2026** tailored to the topic. Generates BibTeX citations and technical dossiers in `artifacts/research/`.
- **Output:** Chapters 1 & 2 drafts citing recent SOTA papers.

### Stage 3: Architecture Specification & C4 Modeling
- **Agent:** `ArchitectAgent`
- **Action:** Designs modular component hierarchy, Pydantic v2 data models, security considerations, and Mermaid sequence/C4 diagrams.
- **Output:** `ArchitectureSpec` + Chapter 3 draft.

### Stage 4: Code-First Implementation & Benchmarking
- **Agents:** `DeveloperAgent` & `ExperimenterAgent`
- **Tools:** `SandboxRunnerTool` (Pytest), `BenchmarkTool` (Matplotlib SVG/PNG), `GitProvenanceTool`.
- **Action:** Implements clean production code (`src/core/`), unit test suites (`tests/`), Dockerfile, and runs empirical load benchmarks (p95 latency).
- **Output:** `List[CodeArtifact]`, `List[BenchmarkResult]`, git commits per stage.

### Stage 5: Dual-Engine Typesetting (Typst & LaTeX)
- **Agent:** `TypesetterAgent`
- **Tool:** `TypesettingTool`
- **Action:** Compiles all chapters, code listings, SVG benchmark figures, and BibTeX into complete, publication-ready documents:
  - `artifacts/thesis/thesis.typ` (Modern Typst format),
  - `artifacts/thesis/thesis.tex` (LaTeX / Overleaf format),
  - `artifacts/thesis/references.bib` (Clean BibTeX).

### Stage 6: Multi-Gate Verification & Reflexion Loop
- **Agent:** `ReviewerAgent` + `MasterVerificationSuite`
- **Action:** Runs all 7 quality gates (Code, Mutation, Citations >= 2023, English naming, Cross-consistency, Style, Stylometry JSA).
- **Reflexion:** If verification score $< 80.0\%$ or any `CRITICAL/ERROR` is raised, execution loops back to the offending stage with targeted repair instructions (*Reflexion* pattern).
