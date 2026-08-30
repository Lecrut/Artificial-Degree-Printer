# ADK Agent Guide

This document explains how an agent should interpret this scaffold and how it should evolve into a modern, extensible harness.

## Expected workflow

1. Read the task description and clarify missing assumptions.
2. Derive structured requirements and success criteria.
3. Select the relevant prompt files, agent role, and tools.
4. Produce a plan before editing files or code.
5. Keep the task decomposition explicit and staged.
6. Execute the task using the available tool layer when needed.
7. Store state, evidence, and logs for each major step.
8. Verify the result before continuing or finalizing.
9. Revise only the affected slice when validation fails.

## Agent design principles

- prefer specialized roles over one overloaded prompt,
- keep the system observable and traceable,
- treat tools as first-class capabilities,
- preserve memory across iterations,
- validate before accepting results,
- prefer incremental improvements over broad, risky changes,
- keep human review available for strategic decisions.

## File responsibilities

- `main.py` - entry point for the runnable program and task bootstrap,
- `adk/state.py` - typed task state and workflow state model,
- `adk/memory_store.py` - persistence for session state and memory,
- `adk/logger.py` - execution log storage and provenance,
- `adk/prompt_catalog.py` - prompt discovery and registry,
- `adk/prompts/` - modular prompt templates for each stage,
- `adk/pipeline/` - workflow design notes and orchestration logic,
- `adk/verification/` - validation rules and quality gates,
- `adk/assets/` - figure and diagram provenance,
- `adk/memory/` - session memory artifacts and project state,
- `adk/logs/` - execution history and review traces.

## Architectural expectations

The project should evolve toward the following model:

- orchestrator manages goals and task graph,
- research agent gathers information and evidence,
- coding agent implements or updates code,
- writing agent produces or revises academic and technical text,
- verification agent checks correctness and completeness,
- human reviewer confirms strategic outcomes or final acceptance.

## Tooling expectation

The system should be conceived as tool-enabled rather than prompt-only. An agent should be able to use:

- file system tools,
- repository tooling,
- terminal execution,
- search and retrieval,
- validation tools,
- external integrations via MCP-compatible interfaces.

## Editing rule

Prefer one small change at a time. If a validation step fails, fix the same slice before widening the scope. Keep changes reviewable and avoid mixing unrelated concerns in a single patch.