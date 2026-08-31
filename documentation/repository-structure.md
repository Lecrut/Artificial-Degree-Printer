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
│   ├── AGENT_GUIDE.md                  # Guidance for writing ADK agents
│   ├── README.md                       # Short introduction to the adk module
│   │
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
│   │   ├── agent_registry.py           # Registry for specialized agents
│   │   ├── context.py                  # ExecutionContext, parallel metrics & tool bindings
│   │   ├── executor.py                 # E2E pipeline run driver
│   │   ├── graph.py                    # StateGraphEngine (Parallel DAG, Re-plan & Swarm)
│   │   ├── harness.py                  # SelfEvolvingHarnessEngine & CrystallizedWorkflows
│   │   ├── logger.py                   # RunLogger to log JSON execution summary
│   │   ├── prompt_catalog.py           # Scan and load prompts from prompt directory
│   │   ├── replay.py                   # DARWIN-REPLAY 2027 Time-Travel Engine
│   │   ├── task_types.py               # TaskTypeRegistry and detect_task_type()
│   │   ├── tool_registry.py            # Dynamic tool registry
│   │   └── workflow.py                 # PipelineStage and TaskGraph definition
│   │
│   ├── graph/                          # Knowledge Graph & Traceability (GraphRAG)
│   │   ├── __init__.py
│   │   └── ontology.py                 # CodeThesisTraceabilityGraph
│   │
│   ├── llm/                            # LLM API Client & ACRouter Model Tiering
│   │   ├── __init__.py
│   │   └── client.py                   # LLMClient & Model Router (Ollama, Gemini, OpenAI)
│   │
│   ├── memory/                         # Persistent Session Storage
│   │   ├── README.md
│   │   └── session.json                # Immutable project session state
│   │
│   ├── templates/                      # Academic Document Blueprints
│   │   ├── latex/                      # Standard LaTeX / Overleaf thesis template
│   │   └── typst/                      # Native Typst 0.11+ thesis template
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
│   │   ├── env_tool.py                 # EnvSecretsManagerTool for secrets setup
│   │   ├── doc_scraper.py              # WebDocumentationScraperTool
│   │   └── git_tool.py                 # Automated git commits per stage
│   │
│   ├── tui/                            # Terminal User Interface
│   │   ├── __init__.py
│   │   └── dashboard.py                # Console status panels
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
├── skills/                             # Composable Agent Skill Specifications
│   ├── adk-sota-paper-ingestor/         # SKILL.md: arXiv/SOTA paper ingestion
│   ├── adk-repo-hygiene-guard/          # SKILL.md: Repository hygiene & Zero 0-Byte guarantee
│   ├── adk-code-quality-auditor/        # SKILL.md: Pydantic v2 & AST test suite auditor
│   └── adk-typst-template-tester/       # SKILL.md: Typst 0.11+ & LaTeX template tester
│
├── tests/                              # Automated Pytest Suite (58 Tests)
│   ├── test_agents.py
│   ├── test_core_models.py
│   ├── test_dynamic_literature_search.py
│   ├── test_e2e_pipeline.py
│   ├── test_git_tool.py
│   ├── test_graph.py
│   ├── test_harness.py
│   ├── test_harness_evolution.py
│   ├── test_interactive_agents.py      # Model-Interactive agent loop tests
│   ├── test_literature_dossier.py
│   ├── test_llm.py
│   ├── test_llm_client.py
│   ├── test_mutation_gate.py
│   ├── test_new_tools.py
│   ├── test_parallel_and_evolution.py  # Parallel execution & progressive crystallization
│   ├── test_project_isolation.py       # Isolated project workspaces tests
│   ├── test_prompt_compiler.py         # Dynamic prompt compiler tests
│   ├── test_replay.py                  # DARWIN-REPLAY 2027 time-travel tests
│   ├── test_repository_hygiene.py      # Repository structural & 0-byte guards
│   ├── test_stylometry.py
│   ├── test_tools.py
│   └── test_verification_gates.py
│
└── documentation/                      # Complete System Documentation
    ├── README.md                       # Documentation index
    ├── methodology_and_roadmap.md      # ADK-TRACE methodology manifest & roadmap
    ├── architecture.md                 # System architecture specification
    ├── workflow.md                     # Execution DAG, Parallelism & Reflexion
    ├── requirements.md                 # Functional and non-functional requirements
    ├── repository-structure.md         # Repository folder and file specification
    ├── project-overview.md             # High-level vision and Code-First paradigm
    ├── build_log_and_changelog.md      # Sequential build log (Etapy 1–18)
    ├── technologies/                   # Production Technology Dossiers & Stack Index
    └── scientific_papers/              # SOTA Paper Dossiers & Search Taxonomy
```
