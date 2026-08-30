# Repository Structure and Database Architecture

This document defines the recommended organization for the project so that it remains understandable, scalable, and easy to maintain. The main principle is strict separation of concerns: state, orchestration, tools, agents, validation, and persistence must be independent modules.

## Design goals

The repository should be designed to avoid large, hard-to-read files and to keep each subsystem responsible for one clearly defined concern.

The project should follow these rules:

- one module = one responsibility,
- one file = one domain concept where possible,
- avoid monolithic files with thousands of lines,
- keep domain logic separate from storage logic,
- keep prompts separate from runtime execution logic,
- keep verification logic separate from agent behavior,
- ensure every task can be tracked, logged, and replayed.

## Recommended folder structure

```text
Artificial-Degree-Printer/
├── README.md
├── requirements.txt
├── main.py
├── pyproject.toml                  # optional, if packaging is introduced later
├── .env.example
├── .gitignore
├── adk/
│   ├── README.md
│   ├── AGENT_GUIDE.md
│   ├── prompts/
│   │   ├── README.md
│   │   ├── 00_system.md
│   │   ├── 01_requirements.md
│   │   ├── 02_planning.md
│   │   ├── 03_generate_code.md
│   │   ├── 04_generate_text.md
│   │   ├── 05_review_response.md
│   │   └── 06_figures.md
│   ├── pipeline/
│   │   ├── README.md
│   │   └── state.md
│   ├── verification/
│   │   ├── README.md
│   │   └── checks.md
│   ├── memory/
│   │   ├── README.md
│   │   └── session.json
│   ├── logs/
│   │   ├── README.md
│   │   └── run-*.json
│   └── assets/
│       ├── README.md
│       └── diagrams/
│
├── app/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── bootstrap.py
│   └── app.py
│
├── core/
│   ├── __init__.py
│   ├── project/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── validators.py
│   ├── session/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── session_manager.py
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── task_graph.py
│   │   ├── planner.py
│   │   ├── state_machine.py
│   │   └── execution_loop.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── store.py
│   │   ├── repositories.py
│   │   ├── models.py
│   │   └── vector_store.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── orchestrator_agent.py
│   │   ├── researcher_agent.py
│   │   ├── architect_agent.py
│   │   ├── coder_agent.py
│   │   ├── writer_agent.py
│   │   ├── reviewer_agent.py
│   │   └── verifier_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── filesystem.py
│   │   ├── terminal.py
│   │   ├── git_tools.py
│   │   ├── search_tools.py
│   │   ├── document_tools.py
│   │   ├── validation_tools.py
│   │   └── mcp_client.py
│   ├── verification/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── checks.py
│   │   ├── rules.py
│   │   ├── report.py
│   │   └── scoring.py
│   ├── provenance/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── trace.py
│   │   └── artifact_store.py
│   └── prompts/
│       ├── __init__.py
│       ├── catalog.py
│       └── loader.py
│
├── infra/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── postgres/
│   │   │   ├── schema.sql
│   │   │   ├── migrations/
│   │   │   │   ├── 001_init.sql
│   │   │   │   └── 002_vector_memory.sql
│   │   │   └── connection.py
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── project_repo.py
│   │       ├── task_repo.py
│   │       ├── artifact_repo.py
│   │       └── memory_repo.py
│   ├── vector/
│   │   ├── __init__.py
│   │   ├── pgvector_client.py
│   │   └── embeddings.py
│   └── observability/
│       ├── __init__.py
│       ├── telemetry.py
│       └── tracing.py
│
├── services/
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── models.py
│   │   └── prompts.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── indexer.py
│   │   └── query.py
│   └── external/
│       ├── __init__.py
│       └── mcp_bridge.py
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_memory_store.py
│   │   ├── test_task_graph.py
│   │   └── test_verification.py
│   ├── integration/
│   │   ├── test_orchestration_flow.py
│   │   └── test_tool_execution.py
│   └── fixtures/
│       ├── sample_project/
│       └── sample_session.json
│
├── docs/
│   ├── README.md
│   └── architecture_notes/
│
└── documentation/
    ├── README.md
    ├── architecture.md
    ├── workflow.md
    ├── requirements.md
    ├── verification.md
    ├── project-overview.md
    ├── repository-structure.md
    └── assets.md
```

## Why this structure is good

This structure keeps responsibilities separated:

- app: command entry and configuration,
- core: main business logic of the agent system,
- infra: database, vector memory, and operational infrastructure,
- services: external model and retrieval integrations,
- tests: validation by scope,
- documentation: project explanation and architecture decisions.

It also prevents a common problem in AI projects: one large file acquiring too many tasks. Instead, each module has a tight responsibility and a smaller surface area.

## Recommended database schema

PostgreSQL should be the main system of record for state, logs, and project metadata. It should store structured data and relationship data. The vector layer can then be used for semantic retrieval and contextual search.

### 1. users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2. projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    project_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3. project_sessions

```sql
CREATE TABLE project_sessions (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    session_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    context JSONB NOT NULL DEFAULT '{}'::jsonb
);
```

### 4. requirements

```sql
CREATE TABLE requirements (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    requirement_text TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 5. tasks

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    session_id UUID REFERENCES project_sessions(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 1,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 6. task_events

```sql
CREATE TABLE task_events (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_message TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 7. agents

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    model_name TEXT,
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 8. tool_calls

```sql
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    tool_name TEXT NOT NULL,
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 9. artifacts

```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    artifact_type TEXT NOT NULL,
    name TEXT NOT NULL,
    storage_path TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 10. verification_results

```sql
CREATE TABLE verification_results (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL,
    score NUMERIC(5,2),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 11. memory_entries

```sql
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    session_id UUID REFERENCES project_sessions(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 12. vector_memory

```sql
CREATE TABLE vector_memory (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    memory_entry_id UUID REFERENCES memory_entries(id) ON DELETE CASCADE,
    embedding VECTOR(1536),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The exact vector dimension depends on the embedding model used. For a modern stack, 1536 is a common default, but this should be adjusted to the actual embedding model.

## Why PostgreSQL is the right main store

PostgreSQL is the right base layer for this project because it keeps all operational relationships in one solid place:

- users and projects,
- tasks and dependencies,
- tool call traces,
- logs and events,
- artifacts and versions,
- verification records,
- semantic memory references.

This structure makes the system auditable, queryable, and much easier to debug. It also keeps future expansion simple without turning the entire project into a single giant JSON blob.

## Modular design principles

To keep the codebase healthy over time, the project should follow these rules:

1. Small files with a single purpose.
2. Domain-specific modules only.
3. Avoid circular imports.
4. Keep database access in repository or infrastructure modules only.
5. Keep business logic out of CLI entry files.
6. Keep the orchestrator separate from agent implementations.
7. Keep validation logic separate from generation logic.
8. Put artifact persistence in a dedicated storage service.

## Practical implementation strategy

Start with these modules first:

- app
- core.orchestration
- core.memory
- core.agents
- core.tools
- core.verification
- infra.db.postgres

Then add the higher-level features:

- vector memory,
- retrieval service,
- advanced semantic search,
- monitoring,
- UI or API layer.

This gives a stable path from MVP to robust multi-agent system without creating a fragile architecture.

## Final recommendation

The project should be organized so that it is easy to reason about, easy to extend, and safe under failure. PostgreSQL should serve as the core state store, while pgvector enables semantic memory. The application layer should remain split across orchestration, agents, tools, verification, and persistence to prevent code bloat and keep responsibilities clean.
