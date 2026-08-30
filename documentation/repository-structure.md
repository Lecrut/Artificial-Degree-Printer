# Repository Structure (ADK 2027)

> **Repository:** `Artificial-Degree-Printer`  
> **Standard:** Modular Python 3.12+ Agentic Framework  
> **Directory Naming Rule:** 100% English Filenames & Zero Polish Diacritics

---

## 1. Actual Implemented Directory Layout

```text
Artificial-Degree-Printer/
├── README.md                           # Main project showcase & quickstart
├── main.py                             # Unified CLI entrypoint (generate, verify, graph)
├── requirements.txt                    # Python runtime dependencies
├── pytest.ini                          # Automated test discovery configuration
│
├── adk/                                # Core ADK 2027 Framework Engine
│   ├── __init__.py
│   ├── agents/                         # Specialized Agent Swarm Roles
│   │   ├── __init__.py
│   │   ├── base.py                     # Abstract BaseAgent interface
│   │   ├── orchestrator.py             # Promotor AI (Intake & Requirements)
│   │   ├── researcher.py               # SOTA literature analyst & dynamic search
│   │   ├── architect.py                # C4 & system architecture designer
│   │   ├── developer.py                # Software engineer & test author
│   │   ├── experimenter.py             # Benchmark & load test analyst
│   │   ├── typesetter.py               # Typst & LaTeX thesis author
│   │   └── reviewer.py                 # Formal critic & gate coordinator
│   │
│   ├── core/                           # Core Data Models & State Persistence
│   │   ├── __init__.py
│   │   ├── models.py                   # Pydantic v2 schemas (Thesis, Reqs, Artifacts)
│   │   ├── state.py                    # Project state & event aggregation
│   │   └── events.py                   # Event Sourcing immutable logs
│   │
│   ├── engine/                         # Orchestration, Context & Harness Evolution
│   │   ├── __init__.py
│   │   ├── graph.py                    # StateGraphEngine (Parallel DAG, Re-plan & Swarm)
│   │   ├── harness.py                  # SelfEvolvingHarnessEngine & CrystallizedWorkflows
│   │   └── context.py                  # ExecutionContext, parallel metrics & tool bindings
│   │
│   ├── graph/                          # Knowledge Graph & Traceability (GraphRAG)
│   │   ├── __init__.py
│   │   └── ontology.py                 # CodeThesisTraceabilityGraph
│   │
│   ├── harness/                        # Task decomposition & scheduling
│   │   ├── __init__.py
│   │   ├── task_graph.py               # Dependency graph validation
│   │   └── tool_registry.py            # Dynamic tool registry
│   │
│   ├── llm/                            # LLM API Client & ACRouter Model Tiering
│   │   ├── __init__.py
│   │   └── client.py                   # LLMClient & ModelTier Router (Tier 1-3)
│   │
│   ├── memory/                         # Persistent Session & Harness Storage
│   │   ├── session.json                # Immutable project session
│   │   ├── harness_repairs.json        # Verified GSME procedural patches
│   │   └── crystallized_workflows.json # Fast-path crystallized templates
│   │
│   ├── templates/                      # Academic Document Blueprints
│   │   ├── thesis.typ                  # Native Typst 0.11+ thesis template
│   │   └── thesis.tex                  # Standard LaTeX / Overleaf thesis template
│   │
│   ├── tools/                          # Model Context Protocol (MCP) Tool Harness
│   │   ├── __init__.py
│   │   ├── base.py                     # BaseTool & ToolResult interfaces
│   │   ├── filesystem.py               # Safe file I/O operations
│   │   ├── sandbox.py                  # Isolated subprocess execution runner
│   │   ├── literature.py               # BibTeX formatting and key validator
│   │   ├── literature_search.py        # Dynamic SOTA paper discovery engine
│   │   ├── literature_dossier.py       # Markdown dossier generator
│   │   ├── benchmarks.py               # Matplotlib vector chart generator
│   │   ├── typesetting.py              # Typst & LaTeX export engine
│   │   └── git_tool.py                 # Automated git commits per stage
│   │
│   ├── tui/                            # Terminal User Interface
│   │   ├── __init__.py
│   │   └── dashboard.py                # Rich console status panels & radars
│   │
│   └── verification/                   # Master Quality Audit Suite (7 Gates)
│       ├── __init__.py
│       ├── code_gate.py                # AST syntax and test validator
│       ├── mutation_gate.py            # Mutation testing engine (MS >= 60%)
│       ├── citation_gate.py            # BibTeX integrity & SOTA horizon (>= 2023)
│       ├── english_naming_gate.py      # Strict English filename enforcer
│       ├── cross_validator.py          # Thesis text vs Codebase AST matcher
│       ├── style_gate.py               # Academic tone and fluff checker
│       └── stylometry.py               # Lexical diversity (TTR) & JSA risk
│
├── artifacts/                          # Generated Project Artifacts & Outputs
│   ├── benchmarks/                     # Vector charts (SVG/PNG) and metrics
│   ├── research/                       # Topic-specific SOTA paper dossiers
│   └── thesis/                         # Compiled Typst, LaTeX & BibTeX files
│
├── generated_project/                  # Generated Target Software Source Code
│   ├── src/core/                       # Production business logic
│   ├── tests/                          # Automated Pytest unit test suite
│   └── Dockerfile                      # Container deployment specification
│
├── skills/                             # Developer & Agent Skill Specifications (2026 Standard)
│   ├── adk-sota-paper-ingestor/         # SKILL.md: Automated arXiv/SOTA paper ingestion
│   │   └── SKILL.md
│   ├── adk-repo-hygiene-guard/          # SKILL.md: Repository cleanup & build log update
│   │   └── SKILL.md
│   ├── adk-code-quality-auditor/        # SKILL.md: Pydantic v2 & AST test suite auditor
│   │   └── SKILL.md
│   └── adk-typst-template-tester/       # SKILL.md: Typst 0.11+ & LaTeX template tester
│       └── SKILL.md
│
├── tests/                              # Automated Pytest Suite (37 Tests)
│   ├── test_agents.py
│   ├── test_core_models.py
│   ├── test_dynamic_literature_search.py
│   ├── test_e2e_pipeline.py
│   ├── test_git_tool.py
│   ├── test_graph.py
│   ├── test_harness.py
│   ├── test_harness_evolution.py
│   ├── test_literature_dossier.py
│   ├── test_llm.py
│   ├── test_mutation_gate.py
│   ├── test_parallel_and_evolution.py  # TIPEX parallel, VMAO replan, TacoMAS swarm
│   ├── test_stylometry.py
│   ├── test_tools.py
│   └── test_verification_gates.py
│
└── documentation/                      # Complete System Documentation
    ├── README.md                       # Documentation index
    ├── methodology_and_roadmap.md      # ADK-TRACE methodology manifest & roadmap
    ├── architecture.md                 # System architecture specification (6 Pillars)
    ├── workflow.md                     # Execution DAG, Parallelism & Reflexion
    ├── verification.md                 # 7-gate quality control & scoring rules
    ├── requirements.md                 # Functional and non-functional requirements
    ├── repository-structure.md         # Repository folder and file specification
    ├── project-overview.md             # High-level vision and Code-First paradigm
    ├── security_and_safety.md          # InjecAgent security threat model & guards
    ├── decision_records.md             # 5 Architecture Decision Records (ADR)
    ├── build_log_and_changelog.md      # Sequential build log (Etapy 1–12)
    └── scientific_papers/              # 36 SOTA Paper Dossiers & Search Taxonomy
        ├── README.md
        ├── search_keywords_taxonomy.md
        ├── architectural_debate_and_synthesis.md
        ├── master_implementation_synthesis.md
        └── *.md (36 analytical dossiers)
```
