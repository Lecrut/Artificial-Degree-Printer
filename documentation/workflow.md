# Execution Workflow & State Transitions (ADK 2027)

> **Workflow Pattern:** Deterministic DAG, Parallel Execution (TIPEX 2026) & Closed-Loop Agentic Reflexion  
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
- **Action:** Generates fully styled academic paper in Typst 0.11+ syntax (`artifacts/thesis/thesis.typ`) and LaTeX (`artifacts/thesis/thesis.tex`) with automated BibTeX linking and vector chart placement (PaperCoder & LongDA Co-Synthesis).
- **Output:** Compiled PDF previews and source `.typ` / `.tex` files.

### Stage 6: Multi-Gate Verification & Closed-Loop Reflexion
- **Agent:** `ReviewerAgent`
- **Engine:** `MasterVerificationSuite` (7 Gates: AST, Mutation, Citations, English Naming, Cross-Consistency, Academic Style, Stylometry TTR).
- **Reflexion Loop:** If any gate fails $\to$ `VerificationIssue` is created $\to$ `SelfEvolvingHarnessEngine` evaluates a `HarnessPatch` $\to$ Gated Evolution (GSME 2026) commits patch $\to$ Retries failed stage via `replan_branch()`.

---

## 3. Ultra-Low-Cost Routing & Progressive Crystallization (2026 SOTA)

### Agent-as-a-Router (ACRouter 2026)
Wykonanie każdego etapu podlega dynamicznemu routingowi modeli (*ModelTier*):
- **Tier 1 (Gemini Flash / SLM):** Etapy 2, 5 i lintery (oszczędność 65-80% kosztu wywołań API).
- **Tier 2 (Standard Code Model):** Etapy 4 i testowanie mutacyjne.
- **Tier 3 (Frontier Reasoning Model):** Etapy 1, 3 oraz głęboka pętla samonaprawy.

### Progressive Workflow Crystallization
Gdy trajektoria wykonawcza danego typu etapu zostanie pomyślnie zweryfikowana co najmniej 3 razy, `CrystallizedWorkflowRegistry` automatycznie przerejestrowuje ją jako skrystalizowany, deterministyczny generator Pythona — redukując wywołanie LLM w kolejnych uruchomieniach o **>70%**.

---

## 4. Standardized SOTA Research & Auto-Implementation Protocol

Dla każdego nowego przełomu naukowego (2023–2026) obowiązuje ściśle określony **4-etapowy protokół postępowania**:

1. **Odkrycie, Analiza i Natychmiastowy Zapis Dossier (Discovery & Dossier Persistence):** Wyszukanie publikacji SOTA i natychmiastowe utworzenie karty analitycznej w `documentation/scientific_papers/<key>.md` oraz aktualizacja indeksiów (`README.md`, `master_implementation_synthesis.md`). Wiedza jest trwale zapisana niezależnie od późniejszego wdrożenia w kodzie.
2. **Propozycja Wdrożenia w Kodzie (Code Approval Gate):** Przedstawienie zwięzłego podsumowania użytkownikowi i zapytanie: *"Karta papieru została zapisana w bazie wiedzy. Czy wdrażamy ten przełom bezpośrednio w kodzie i głównej dokumentacji?"*.
3. **Implementacja Kodowa i Testy (Code & Test):** Po uzyskaniu zgody ("tak") — zaimplementowanie funkcji w `adk/` oraz napisanie testów w `tests/` (100% PASS).
4. **Pełna Aktualizacja Dokumentacji Głównej (Full Core Docs Sync):** 
   - Zaktualizowanie wszystkich plików dokumentacji głównej (`architecture.md`, `methodology_and_roadmap.md`, `requirements.md`, `repository-structure.md`, `project-overview.md`).
   - Dopisanie sekwencyjnego etapu do `build_log_and_changelog.md` (bez przeskakiwania numerów).
