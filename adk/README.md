# ADK (Autonomous Degree Kit) Engine

The `adk` package is the core execution framework for the **Artificial-Degree-Printer** system, automating end-to-end software synthesis, empirical benchmarking, literature research, and academic thesis typesetting.

---

## 📦 Package Architecture

```
adk/
├── agents/         # Multi-Agent Swarm (Orchestrator, Researcher, Architect, Developer, Experimenter, Typesetter, Reviewer)
├── core/           # Pydantic v2 Models, Immutable State, and Event Sourcing (ADKProjectState, EventLog)
├── engine/         # Execution Context, StateGraph DAG, Self-Evolving Harness, Prompt Compiler, DARWIN-REPLAY
├── graph/          # Code-Thesis Traceability Graph & Coverage Analyzer (GraphRAG / Ontology)
├── llm/            # Topaz Complexity Estimator & ACRouter Multi-Tier LLM Client (Ollama, Gemini, Fallback)
├── memory/         # Session State Persistence (MemoryStore & session.json)
├── prompts/        # Dynamic Prompt Catalog (00_system through 06_figures with REprompt assertions)
├── templates/      # Academic Document Blueprints (Typst 0.11+ and LaTeX/Overleaf templates)
├── tools/          # Model Context Protocol (MCP) Tool Harness (FileSystem, Sandbox, Git, Benchmarks, Scraper, etc.)
├── tui/            # Rich Terminal User Interface Dashboard
├── web/            # Web Dashboard & Live Thesis Viewer (FastAPI & Zero-Dependency SPA)
└── verification/   # Master Quality Audit Suite (7 Verification Gates)
```

---

## 🚀 Key Modules

- **`adk.agents`**: Specialized agent implementations coordinating across the 7 pipeline phases, featuring the **Open-Ended Dynamic Polyglot Engine** (`DeveloperAgent` & `DynamicLanguageResolver`) capable of discovering, scaffolding, and implementing projects in any programming language (Zig, Elixir, Haskell, Scala, Julia, Kotlin, Swift, Rust, Go, TS, Python, C++, C#, Mojo, etc.).
- **`adk.engine.executor`**: `ADKE2EExecutor` orchestrating the full pipeline with TIPEX 2026 parallel execution.
- **`adk.engine.context`**: `ExecutionContext` managing isolated project workspaces under `projects/<project_id>/`.
- **`adk.engine.graph`**: `StateGraphEngine` providing deterministic DAG execution, speculative execution, and VMAO branch replanning.
- **`adk.web`**: `start_web_server` uruchamiający nowoczesny interfejs Web Dashboard & Live Thesis Viewer (`python main.py web`).
- **`adk.verification`**: 7-gate verification suite zapewniający uniwersalną walidację kodu, mutacje ($\ge 60\%$), cytowania ($\ge 2023$), angielskie nazewnictwo, spójność i stylometrię.