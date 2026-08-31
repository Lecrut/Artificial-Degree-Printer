# System Architecture (ADK 2027)

> **Standard:** 2027 Multi-Agent Software & Academic Thesis Generation Architecture  
> **Methodology:** ADK-TRACE (Traceable, Reflexive, Artifact-Centric Engineering)  
> **Theoretical Foundation:** 37 Seminal SOTA Papers (2023–2026 SOTA Horizon)  
> **Production Tech Stack:** 12 SOTA Technologies (`documentation/technologies/`)  
> **Core Equation:** $\text{Autonomous Agent} = \text{Base LLM Model} + \text{Agent Harness}$ (Harness Engineering Paradigm 2026/2027)

---

## 1. High-Level Architectural Vision

`Artificial-Degree-Printer` (ADK) is designed as a **deterministic, tool-augmented, multi-agent harness** rather than a single monolithic prompt. The platform realizes the **Code-First & Empiricism-Driven** paradigm: academic theses (Engineering & Master's) and technical documentation are generated as an empirical audit and rigorous documentation of real, sandboxed, compiled, and benchmarked software artifacts.

```
                           ADK 2027 MULTI-TIER ARCHITECTURE
  
  [ 1. INTERFACE PLANE ]   CLI Terminal / Rich TUI Dashboard / JSON API / HITL Gates
             │
             ▼
  [ 2. ORCHESTRATION ]     StateGraph DAG Engine (Parallel TIPEX, Re-plan VMAO, PASTE 2026 Speculation)
             │
             ▼
  [ 3. AGENT SWARM ]       Promotor AI ── Researcher ── Architect ── Developer
                                       ── Experimenter ── Typesetter ── Reviewer
             │
             ▼
  [ 4. TOOL HARNESS ]      Model Context Protocol (MCP) ── SandboxRunner (WASI 0.2 / Subprocess)
                           ── BenchmarkTool (Polars/DuckDB/SVG) ── TypesettingEngine (Typst 0.11+/CeTZ)
             │
             ▼
  [ 5. TRACE & MEMORY ]    CodeThesisTraceabilityGraph (GraphRAG/LanceDB) ── Session Store (JSON)
             │
             ▼
  [ 6. QUALITY GATES ]     MasterVerificationSuite (AST, Citations, Mutmut MS >= 60%, JSA Stylometry)
```

---

## 2. Core Architectural Layers & 2027 Modern Tooling

### 1. Interface & Control Plane (`adk/tui/`, `main.py`)
- **Rich Terminal TUI Console**: Live interactive visual rendering of project status, component tables, quality radars, and artifact paths (`TerminalDashboard`).
- **CLI Subcommands**: `generate <topic>`, `verify`, `graph`.
- **Human-in-the-Loop (HITL) Checkpoints**: Promotor review approval gates after SOTA research and architecture specification.

### 2. Deterministic Orchestration Plane (`adk/engine/`)
- **StateGraph Engine (`graph.py`)**: Directed Acyclic Graph (DAG) for deterministic stage transitions.
- **Two-Tier Inference Parallelism (`execute_parallel()`)**: Concurrent execution of unblocked DAG steps (4.5x wall-clock speedup).
- **Branch-Level Replanning (`replan_branch()`)**: Re-executes exclusively the affected stage and its dependents upon verification failure.
- **Birth-Death Node Swarm (`spawn_specialist_node()`, `retire_node()`)**: Runtime specialist sub-agent creation and unregistration.
- **Act While Thinking Speculative Tool Execution (`execute_speculative_tools()`)**: Pre-fetches BibTeX, Typst templates, and AST checks while LLM streams thoughts (48.6% latency reduction).

### 3. Agent Swarm Plane (`adk/agents/`)
- **7 Specialized Roles**: `OrchestratorAgent` (Promotor AI), `ResearcherAgent`, `ArchitectAgent`, `DeveloperAgent`, `ExperimenterAgent`, `TypesetterAgent`, `ReviewerAgent`.
- **Typed Pydantic Substrate**: All inter-agent messages pass via Pydantic v2 models (`adk/core/models.py`).

### 4. Tool & Sandbox Harness (`adk/tools/`)
- **Anthropic MCP Compliance (`base.py`)**: Unified tool contract returning structured `ToolResult` schemas.
- **Isolated Sandbox Execution (`sandbox.py`)**: Executes Pytest unit test suites in an isolated environment with 30s hard timeouts and `_safe_path` traversal guards.
- **Dual-Engine Typesetting (`typesetting.py`)**: Simultaneously exports **Typst 0.11+** (`thesis.typ`) with CeTZ diagrams and **LaTeX** (`thesis.tex`) with BibTeX.
- **Empirical Benchmarking (`benchmarks.py`)**: Generates vector SVG/PNG charts for p95 latency under simulated client loads (Polars & DuckDB integration).
- **Interactive Secrets & Env Manager (`env_tool.py`)**: Autonomously creates `.env.example` and `.env` files, prompting the user via HITL Checkpoints for required API keys.
- **Live Web Documentation Scraper (`doc_scraper.py`)**: Scraping latest documentation snippets directly from official tech web pages (Next.js 15, FastAPI, React 19, Typst 0.11+).

### 5. Knowledge Graph & Memory Plane (`adk/graph/`, `adk/memory/`)
- **CodeThesisTraceabilityGraph (`ontology.py`)**: GraphRAG & Tree-Sitter AST ontology mapping `Requirements -> Code AST -> Pytest -> Benchmarks -> Thesis Chapters -> SOTA Citations`.
- **Persistent Session & Harness Memory (`session.json`, `harness_repairs.json`, `crystallized_workflows.json`)**: Preserves session state and verified GSME procedural patches across executions.

### 6. Master Quality Audit Suite (`adk/verification/`)
- **7-Gate Audit Engine**:
  1. `CodeVerificationGate` (Python AST syntax parsing & packaging checks)
  2. `MutationTestingGate` (Mutmut mutation score $MS \ge 60\%$)
  3. `CitationVerificationGate` (BibTeX integrity & max 3-year SOTA horizon $\ge 2023$)
  4. `EnglishNamingVerificationGate` (Strict 100% English filenames & zero Polish diacritics)
  5. `CrossConsistencyValidator` (Thesis text AST symbol matching against generated code)
  6. `AcademicStyleGate` (Academic tone & AI fluff elimination)
  7. `StylometryAuditGate` (Type-Token Ratio $TTR \ge 0.35$ & estimated JSA plagiarism risk)

---

## 3. Technology Stack Reference

For detailed analytical dossiers on all 12 production technologies utilized in ADK and generated IT projects (`src/core/`), see **[`documentation/technologies/`](technologies/README.md)**.
