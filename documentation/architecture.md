# Architecture

## High-level goal

The project should be structured as an agent harness rather than a single monolithic prompt. The central idea is that an AI system for research and technical project generation needs a robust execution environment: a planner, memory, tool adapters, validation loops, and a clear model of project state.

## Architectural layers

### 1. Interface layer
This layer handles user interaction and project intake.

It includes:

- task description and requirement capture,
- user context, constraints, and review feedback,
- domain selection (e.g. thesis, software project, research report),
- human approval checkpoints.

### 2. Orchestration layer
This is the central control plane of the system.

Responsibilities:

- decomposing a high-level request into work items,
- choosing which agent or tool to invoke,
- tracking stage dependencies and retries,
- selecting validation gates,
- deciding whether to continue, revise, or escalate to human review.

This layer should be designed as a state machine or task graph rather than a simple sequential script.

### 3. Agent layer
Specialized agents provide focused expertise.

Recommended roles:

- orchestrator: manages workflow and priorities,
- researcher: searches for information, evidence, and prior work,
- architect: determines the technical structure and design choices,
- implementer: writes code, config, and project files,
- writer: drafts sections, explanations, and publication-quality prose,
- reviewer: checks coherence and requirement coverage,
- verifier: executes tests, checks, and evaluation logic.

Each agent should have clear boundaries and tool permissions.

### 4. Tool layer
The tool layer turns the agent into a real operating system for project work.

Suggested categories:

- repository tools: git, file reading, file writing, diff review,
- execution tools: terminal commands, build/test runners,
- search tools: web search, local search, RAG index,
- browser tools: retrieving sources and documentation,
- data tools: database or vector store access,
- document tools: PDF generation, markdown validation, citations,
- validation tools: linting, type checking, unit tests, style checks,
- MCP-compatible tool servers for external systems.

This is a major modern requirement: the agent should be able to use tools instead of only generating text.

### 5. Memory and knowledge layer
The system needs a strong memory substrate to remain useful across multiple runs and long tasks.

This layer stores:

- session state and execution metadata,
- task decomposition and revision history,
- relevant project files and generated artifacts,
- research notes, sources, and evidence,
- previous project decisions and lessons learned,
- user preferences and accepted standards.

Memory should include both short-term working memory and longer-term project memory.

### 6. Validation and evaluation layer
This layer ensures that generated outputs are not accepted blindly.

It should include:

- syntax and build validation,
- semantic checks against requirements,
- technical correctness and consistency checks,
- scientific writing checks such as argument flow and structure,
- evaluation metrics for quality, completeness, and factual support,
- human review gates for higher-risk or final decisions.

### 7. Artifact and provenance layer
This layer records what was produced and why.

Artifacts may include:

- source code,
- reports and thesis chapters,
- diagrams and figures,
- test results,
- verification logs,
- review comments,
- traceability to requirements.

Provenance is essential for trustworthy academic and technical outputs.

## Core design principles

- modularity: separate orchestration, tools, memory, and validation,
- extensibility: easy to add agents, tools, and constraints,
- observability: logs, traces, and state snapshots should remain inspectable,
- verification-first: do not accept a result without a quality gate,
- tool abstraction: agents should interact using capabilities, not ad hoc scripts,
- human oversight: important decisions remain reviewable and controllable,
- traceability: every output can be linked back to evidence and requirements.

## Reference architecture

A plausible modern structure for this project is:

1. User request enters the system.
2. The orchestrator interprets the task and creates a task graph.
3. The planner selects relevant agents and tools.
4. Research and design agents gather needed context.
5. Implementation agents modify files, code, or documents.
6. Validation agents run checks and produce evidence.
7. The orchestrator decides whether to iterate or finalize.
8. Results and logs are stored with provenance metadata.

## Recommended technical stack

For the first production-grade version, the project should favor a practical and extensible stack:

- Python as the orchestration and service layer,
- PostgreSQL as the structural memory store,
- pgvector as the semantic memory layer for similarity search and retrieval,
- Redis for queueing or transient workflow coordination when needed,
- JSON or SQLAlchemy models for state and project metadata,
- MCP-compatible interfaces for tool integration,
- file-system and terminal adapters for code and document work,
- CLI-first execution before building a web app.

This stack is modern, reliable, and easy to expand as the system grows.

## Component specification

### Core runtime

The core runtime should provide:

- configuration loading,
- session bootstrap,
- task orchestration,
- agent execution loop,
- logging and lifecycle management,
- connectivity to the memory and tool layers.

### Memory layer

The memory layer should cover:

- project metadata,
- task state and dependency graph,
- agent decisions and observations,
- prior run history,
- structured notes and evidence,
- retrieval data for future similarity matching.

### Tool and action layer

Every agent should interact through a tool registry exposing operations such as:

- read file,
- write file,
- search repository,
- run shell command,
- run tests,
- inspect git diff,
- fetch research sources,
- validate document structure,
- call external MCP tools.

### Verification layer

The verification layer should produce explicit evidence rather than implicit trust. It should capture:

- test results,
- type or lint output,
- requirement coverage,
- document consistency checks,
- issue lists with severity and stage location,
- revision recommendation when fail conditions are detected.

## Implementation phases

### Phase 1: foundation

- define core data model,
- create project and session lifecycle,
- implement task orchestration,
- create log persistence,
- establish the first validation pass.

### Phase 2: tool-enabled workflow

- add filesystem and terminal adapters,
- enable repo-aware code editing,
- add lint/test execution,
- wire review and revise loops,
- add API/CLI interfaces.

### Phase 3: knowledge layer

- add Postgres-backed memory store,
- integrate pgvector for semantic retrieval,
- store evidence, notes, and prior outputs,
- support contextual recall for future runs.

### Phase 4: specialization

- create distinct specialist agents,
- route tasks by role and tool needs,
- add human review checkpoints,
- define escalation policies.

### Phase 5: production hardening

- metrics and telemetry,
- safe execution constraints,
- versioned artifacts,
- deployment support,
- observability and operational control.

## Why this is a modern architecture

This approach aligns with current trends in 2025-2027 AI system design:

- model + tool ecosystem, not model alone,
- explicit orchestration and memory,
- specialized agents for different functions,
- use of standardized connectors such as MCP,
- emphasis on verification, evaluation, provenance, and traceability,
- support for iterative human-AI collaboration.

## Evolution path

The project can begin as a minimal scaffold and grow into a richer system in layers:

1. simple prompt-driven workflow,
2. persistent memory and state,
3. tool execution layer,
4. multi-agent orchestration,
5. verification and scoring,
6. workflow automation and sandboxing,
7. production-quality observability and governance.

This path keeps the repository practical while aligning it with the expected direction of agentic software in the coming years.
