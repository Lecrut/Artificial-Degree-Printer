# Artificial Degree Printer

Artificial Degree Printer is a research-oriented agentic framework for generating and refining software projects, academic work, and technical documentation with AI assistance. The goal is not just to produce one-off text or code, but to create a reusable agentic system capable of collaborating with tools, validating outputs, storing context, and improving itself over time.

## Mission

The system is designed to support a semi-autonomous workflow that:

- receives an initial user request, constraints, and domain context,
- decomposes complex work into structured tasks,
- invokes specialized AI agents and external tools,
- produces code, documentation, thesis sections, and research artifacts,
- validates the results using tests, quality checks, and review loops,
- preserves state, evidence, and decision traces across iterations,
- revises the output when requirements or feedback change.

## Why this project matters

Modern AI systems are no longer just chat assistants. The most effective systems in 2027 combine:

- orchestration of multiple specialized agents,
- tool use via a standardized protocol such as MCP,
- persistent memory and context tracking,
- sandboxed execution for code and artifacts,
- explicit evaluation loops and verification gates,
- human-in-the-loop review and acceptance criteria,
- structured provenance for scientific claims and engineering decisions.

This repository is designed around the 2027-style pattern for modern AI systems: a harness for building an agent that can generate academic writing and technical software deliverables while remaining observable, safe, extensible, and tool-driven.

## Core concept

The project is centered around an agentic writing-and-building platform for the following use cases:

- generating or improving a thesis or scientific article,
- creating a software project or technical prototype from a requirement,
- writing documentation, architecture, tests, and reports,
- organizing research questions, evidence, citations, and structured findings,
- iterating on the result through review, verification, and correction cycles.

The system behaves like a small research-and-engineering lab: one orchestrator coordinates several specialized roles, each with a clear scope and toolset.

## 2027-style architectural direction

The project should evolve toward a tool-driven agent architecture with the following characteristics, matching the direction of modern AI engineering in 2027:

- orchestrator agent: manages tasks, dependencies, execution state, retries, and handoffs,
- research agent: gathers evidence, sources, related work, and technical context,
- architecture agent: shapes the system design, structure, and engineering decisions,
- coding agent: generates or modifies code, tests, and config files,
- writing agent: drafts academic prose, sections, abstracts, and conclusions,
- review agent: checks consistency, quality, and factual alignment,
- verification agent: runs tests, inspections, validation, and risk checks,
- human reviewer: confirms strategic decisions or accepts final output.

The architecture should be built around a tool registry and execution layer where each agent can call the tools it needs without hardcoding everything into a single prompt, following the 2027 model of agentic systems: orchestration + memory + tools + validation + observability.

## Tooling model

The system is expected to support a modular tool ecosystem such as:

- file system tools for reading and editing project files,
- repository tools for git, diff review, and change tracking,
- search tools for web research, code search, and paper lookup,
- browser or retrieval tools for evidence gathering,
- terminal tools for running build/test commands,
- validation tools for linting, type checking, and test execution,
- documentation tools for structure and consistency checks,
- database or memory tools for long-term knowledge persistence,
- external connectors using MCP-compatible interfaces.

This is the key design idea: the agent is not just a model with a prompt; it is a model connected to a harness of tools that give it real operational capabilities, including filesystem access, repo actions, terminal execution, retrieval, validation, and MCP-compatible integrations.

## Memory and state model

The system should keep structured state for every execution:

- user request and original goals,
- requirements and constraints,
- decomposition into tasks and stages,
- plan history and branch decisions,
- tool invocations and their outcomes,
- intermediate artifacts and generated files,
- verification results and failure reasons,
- final accepted state and evidence trail.

This state layer is what turns a fragile demo into a controllable, auditable engineering system.

## Verification-first principle

The project should adopt a verification-before-acceptance model:

- no final output without a check of the result,
- each stage has a validation pass,
- if tests or checks fail, the system revises the relevant component instead of blindly continuing,
- evidence must be stored to explain why a revision was made.

This principle is critical for technical work and academic writing, because correctness and traceability are equally important.

## Documentation

The full project description is available in [documentation/README.md](documentation/README.md).

## Repository structure

- [adk/](adk/) - agent scaffolding, prompt catalog, memory, logs, and workflow notes
- [adk/prompts/](adk/prompts/) - modular prompts for each stage
- [adk/pipeline/](adk/pipeline/) - workflow design and orchestration notes
- [adk/verification/](adk/verification/) - validation rules and quality controls
- [adk/memory/](adk/memory/) - state and working memory
- [adk/logs/](adk/logs/) - execution logs and decision traces
- [adk/assets/](adk/assets/) - diagrams, figures, and provenance metadata
- [documentation/](documentation/) - architecture, requirements, workflow, and verification documents

## Minimal run

```bash
python main.py "Create a small system for automated thesis and project generation"
```

The script stores the current execution state in [adk/memory/session.json](adk/memory/session.json) and logs the run in [adk/logs/](adk/logs/).

## Design principles

This project is intended to be understandable to both humans and agent systems. The main principles are:

- modular prompts and specialist roles,
- explicit task decomposition,
- persistent state and memory,
- tool-augmented execution,
- verification before acceptance,
- traceable changes and logged decisions,
- consistent alignment between code, documentation, literature, and visuals,
- extensibility for new tools, agents, and workflows.

## Recommended future directions

The project should evolve in stages:

1. MVP agent harness with a single orchestrator and minimal tool layer.
2. Multi-agent specialization for research, coding, writing, and review.
3. Real tool integration using MCP, browser access, and code execution.
4. RAG and structured memory for literature, prior project state, and domain context.
5. Verification and evaluation scoring for generated outputs.
6. Human-in-the-loop review and final acceptance workflow.
7. Production-grade telemetry, artifact versioning, and safe execution sandboxing.

## Implementation roadmap

The project should be built in phases, with the most important work concentrated on the architecture of memory, orchestration, and verification. The recommended priority order is:

### Phase 1 - foundation and state

- define the core project/session/task model,
- create a memory store for requirements, decisions, logs, and task status,
- design the task graph and stage orchestration,
- create the initial agent registry and execution loop,
- establish basic verification and logging flows.

This phase is the bedrock of the platform. If it is weak, every later layer becomes fragile.

### Phase 2 - tools and execution

- add filesystem, terminal, git, and validation tools,
- connect agent actions to real project files and commands,
- add quality checks for code, docs, and project structure,
- support retries and stage-level correction loops,
- expose basic CLI or API entry points for interaction.

This phase turns the system from a prompt-powered assistant into a real operational agent.

### Phase 3 - research and knowledge layer

- add structured project memory and retrieval memory,
- integrate PostgreSQL as the primary state store,
- add pgvector or another vector layer for semantic search,
- store evidence, prior project notes, and source metadata,
- support literature and technical context retrieval.

This is where the project becomes especially useful for thesis writing and research-driven technical tasks.

### Phase 4 - multi-agent specialization

- split responsibilities into researcher, architect, coder, writer, reviewer, and verifier,
- assign tasks to the relevant agent based on the current stage,
- add controlled handoff between agents,
- keep a human approval gate for important decisions and final outputs.

### Phase 5 - production polish

- monitoring and tracing,
- artifact versioning,
- safe execution environments,
- caching and performance tuning,
- governance for tool permissions and review logs,
- deployment support for local or remote workflows.

## Recommended technical foundation

For this project, the strongest starting stack is:

- Python for orchestration and agent logic,
- PostgreSQL as the primary structured memory layer,
- pgvector for semantic retrieval and similarity search,
- Redis or a lightweight queue for async task flow when needed,
- JSON or structured models for session state,
- MCP-compatible tool interfaces for extensibility,
- CLI-first execution before a full UI.

This combination gives strong durability, traceability, and extensibility without overengineering the initial version.

## Status

This repository is a structured foundation for building a modern agentic system for research and software generation. It already establishes the core idea, but the next step is to convert it from a conceptual scaffold into a tool-rich operational harness with orchestration, memory, verification, and agent specialization.