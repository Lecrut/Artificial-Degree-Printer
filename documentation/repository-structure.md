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
│   ├── engine/                         # Orchestration & Context
│   │   ├── __init__.py
│   │   ├── graph.py                    # StateGraphEngine DAG & Reflexion loop
│   │   └── context.py                  # ExecutionContext & tool bindings
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
│   ├── llm/                            # LLM API Client & Fallback Engine
│   │   ├── __init__.py
│   │   └── client.py
│   │
│   ├── memory/                         # Persistent Session Storage
│   │   └── session.json
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
├── tests/                              # Automated Pytest Suite (28 Tests)
│   ├── test_agents.py
│   ├── test_core_models.py
│   ├── test_dynamic_literature_search.py
│   ├── test_e2e_pipeline.py
│   ├── test_git_tool.py
│   ├── test_graph.py
│   ├── test_harness.py
│   ├── test_literature_dossier.py
│   ├── test_llm.py
│   ├── test_mutation_gate.py
│   ├── test_stylometry.py
│   ├── test_tools.py
│   └── test_verification_gates.py
│
└── documentation/                      # Complete System Documentation
    ├── README.md                       # Documentation index
    ├── methodology_and_roadmap.md      # ADK-TRACE methodology manifest & roadmap
    ├── architecture.md                 # System architecture specification
    ├── workflow.md                     # 6-stage execution DAG & reflexion loops
    ├── verification.md                 # 7-gate quality control & scoring rules
    ├── requirements.md                 # Functional and non-functional requirements
    ├── repository-structure.md         # Repository folder and file specification
    ├── project-overview.md             # High-level vision and Code-First paradigm
    ├── assets.md                       # Visual asset standards
    └── scientific_papers/              # 17 SOTA Paper Dossiers & Architectural Debate
        ├── README.md
        ├── architectural_debate_and_synthesis.md
        ├── master_implementation_synthesis.md
        └── *.md (17 analytical dossiers)
```
