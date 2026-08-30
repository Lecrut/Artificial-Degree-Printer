# System Architecture (ADK 2027)

> **Standard:** 2027 Multi-Agent Software & Academic Thesis Generation Architecture  
> **Methodology:** ADK-TRACE (Traceable, Reflexive, Artifact-Centric Engineering)  
> **Theoretical Foundation:** 17 Seminal SOTA Papers (2023–2026)
> **Theoretical Foundation:** 36 Seminal SOTA Papers (2023–2026 SOTA Horizon)  
> **Core Equation:** $\text{Autonomous Agent} = \text{Base LLM Model} + \text{Agent Harness}$ (Harness Engineering Paradigm 2026/2027)

---

## 1. High-Level Architectural Vision

`Artificial-Degree-Printer` (ADK) is designed as a **deterministic, tool-augmented, multi-agent harness** rather than a single monolithic prompt. The platform realizes the **Code-First & Empiricism-Driven** paradigm: academic theses (Engineering & Master's) and technical documentation are generated as an empirical audit and rigorous documentation of real, sandboxed, compiled, and benchmarked software artifacts.

```
                           ADK 2027 MULTI-TIER ARCHITECTURE
  
  [ 1. INTERFACE PLANE ]   CLI Terminal / Rich TUI Dashboard / JSON API / HITL Gates
             │
             ▼
  [ 2. ORCHESTRATION ]     StateGraph DAG Engine (SOPs, Dependencies, Reflexion Loops)
             │
             ▼
  [ 3. AGENT SWARM ]       Promotor AI ── Researcher ── Architect ── Developer
                                       ── Experimenter ── Typesetter ── Reviewer
             │
             ▼
  [ 4. TOOL HARNESS ]      Model Context Protocol (MCP) ── SandboxRunner (Pytest)
                           ── BenchmarkTool (SVG/PDF) ── TypesettingEngine (Typst/LaTeX)
             │
             ▼
  [ 5. TRACE & MEMORY ]    CodeThesisTraceabilityGraph (GraphRAG) ── Session Store (JSON)
             │
             ▼
  [ 6. QUALITY GATES ]     MasterVerificationSuite (AST, Citations, Mutation, JSA Stylometry)
```

---

## 2. Core Architectural Layers & 2027 Modern Tooling

### 1. Interface & Control Plane (`adk/tui/`, `main.py`)
- **Rich Terminal TUI Console**: Live interactive visual rendering of project status, component tables, quality radars, and artifact paths (`TerminalDashboard`).
- **CLI Subcommands**: `generate <topic>`, `verify`, `graph`.
- **Human-in-the-Loop (HITL) Checkpoints**: Promotor review approval gates after SOTA research and architecture specification.

### 2. Deterministic Orchestration Plane (`adk/engine/`)
- **StateGraph Engine** (inspired by *MetaGPT* & *Agentless*): Directed Acyclic Graph (DAG) with explicit state transition contracts and retry/reflexion loops on verification failure.
- **ExecutionContext**: Decoupled environment managing tool bindings, session storage, and workspace directories.

### 3. Specialized Multi-Agent Swarm (`adk/agents/`)
- **Promotor AI (`OrchestratorAgent`)**: High-level problem decomposition, MoSCoW requirements definition (`REQ-F-xx`, `REQ-NF-xx`).
- **Literature Researcher (`ResearcherAgent`)**: Dynamic SOTA research ($\ge 2023$, top citations), BibTeX compilation, and implementation backlog extraction.
- **System Architect (`ArchitectAgent`)**: C4 model design, Pydantic data schemas, sequence diagrams, and security analysis.
- **Software Engineer (`DeveloperAgent`)**: Production-grade modular code (`src/core/`), unit test suites (`tests/`), and container packaging (`Dockerfile`).
- **Benchmark Analyst (`ExperimenterAgent`)**: SLA latency measurements under load, raw datasets, and vector charts.
- **Academic Typesetter (`TypesetterAgent`)**: Complete thesis composition in **Typst** and **LaTeX** (Tectonic/Overleaf ready).
- **Formal Critic (`ReviewerAgent`)**: Multi-gate quality audit, AST cross-verification, and anti-hallucination verification.

### 4. Tool & Execution Harness (`adk/tools/`)
- **Model Context Protocol (MCP)** (Standard *Anthropic MCP* & *Toolformer*): Standardized JSON-RPC tool contracts.
- **Sandbox Execution Runner (`SandboxRunnerTool`)**: Isolated process execution with strict timeouts, environment controls, and stdout/stderr capture.
- **Vector Benchmark Generator (`BenchmarkTool`)**: Matplotlib 300 DPI vector charts (SVG/PNG/PDF) and JSON metrics.
- **Dual-Engine Typesetter (`TypesettingTool`)**: Native **Typst 0.11+** generator and **LaTeX / BibLaTeX** compiler.
- **Automated Git Provenance (`GitProvenanceTool`)**: Granular git commit history tagged per agent stage.

### 5. Knowledge & Traceability Layer (`adk/graph/`, `adk/core/`)
- **CodeThesisTraceabilityGraph (GraphRAG)**: Full ontology mapping:
  $$\text{Requirement} \longrightarrow \text{Code File} \longrightarrow \text{Unit Test} \longrightarrow \text{Benchmark} \longrightarrow \text{Chapter} \longrightarrow \text{Citation}$$
- **Event Sourcing Memory (`adk/core/events.py`)**: Immutable log of every agent action and tool call.

### 6. Verification & Anti-Hallucination Gate (`adk/verification/`)
- **`CodeVerificationGate`**: AST syntax validation and mandatory unit test coverage.
- **`MutationTestingGate`**: Mutation testing engine calculating Mutation Score ($MS \ge 60\%$).
- **`CitationVerificationGate`**: BibTeX integrity validation and strict SOTA horizon enforcement ($\ge 2023$ r.).
- **`EnglishNamingVerificationGate`**: Verification of strict English filenames across the entire repository.
- **`CrossConsistencyValidator`**: AST symbol matching between thesis text descriptions and codebase classes/functions.
- **`StylometryAuditGate`**: Lexical diversity ($TTR$), sentence variance, and JSA anti-plagiarism pre-check.

---

## 3. Technology Stack Summary (2027 Standard)

| Komponent / Warstwa | Zastosowana Nowoczesna Technologia |
| :--- | :--- |
| **Język Główny** | Python 3.12+ (z pełnym typowaniem `typing`, dataclasses, slots) |
| **Modele Danych i Walidacja** | Pydantic v2 (ścisłe schematy wejść/wyjść) |
| **Silnik Składu Akademickiego** | **Typst 0.11+** (główny) + **LaTeX / BibLaTeX** (eksport Overleaf) |
| **Wizualizacja Naukowa** | Matplotlib 3.10+ (wektorowe wykresy SVG/PDF, 300 DPI, styl akademicki) |
| **Interfejs Konsolowy** | Rich 13.9+ (kolorowe panele, tabele statusu, radary jakości) |
| **Testowanie i Piaskownica** | Pytest 9.1+, Subprocess Sandbox z timeoutem, AST Parser |
| **Wersjonalizacja** | Git CLI z automatycznymi commitami per etap agenta |
| **Standard Integracji Narzędzi** | Model Context Protocol (MCP) kompatybilny standard JSON Schema |
