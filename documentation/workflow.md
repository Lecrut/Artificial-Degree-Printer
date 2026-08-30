# Workflow

## Overview

The project should operate as a structured agent workflow with explicit stages, dependency-aware execution, and controlled revision loops. The goal is not to run everything in a single prompt, but to turn a complex task into a manageable set of steps with evidence and feedback at each stage.

## Core execution pipeline

### 1. Intake and framing

- collect the user request,
- identify the task type: thesis, project generation, research report, code implementation, or documentation update,
- extract explicit requirements, constraints, deadlines, and domain context,
- define success criteria and acceptance conditions.

### 2. Context gathering

- read the existing project state,
- inspect relevant files, prompts, and memory,
- collect prior notes or previous runs,
- identify missing information and research needs,
- decide whether external tools or research are required.

### 3. Planning and decomposition

- break the problem into a task graph or ordered stages,
- assign responsibilities to agents and tools,
- identify dependencies between writing, coding, and validation tasks,
- determine the best execution order and likely failure points,
- define checkpoints for human review when necessary.

### 4. Research and evidence collection

- gather source material, prior work, technical references, and domain facts,
- synthesize research findings into structured notes,
- identify contradictions, knowledge gaps, or unresolved assumptions,
- store evidence in a traceable memory layer.

### 5. Generation and composition

- create or update the project structure,
- implement software files, configs, tests, and documentation,
- draft thesis sections, technical descriptions, and conclusions,
- create diagrams or visual assets when required.

### 6. Verification and quality control

- run code checks, tests, linting, build steps, and consistency validation,
- verify that the output matches the requirements,
- review whether the narrative is coherent and evidence-based,
- look for missing elements, contradictions, or low-quality reasoning.

### 7. Revision loop

- identify the exact failing stage or weak section,
- revise only the relevant artefacts,
- re-run the appropriate validation checks,
- continue repeating until the output reaches the acceptance threshold.

### 8. Finalization and memory save

- store final artifacts and decisions,
- record the execution log, state, and rationale,
- preserve the project memory for future iterations,
- optionally present the result to a human reviewer for final approval.

## Execution model

The system should evolve from a simple linear pipeline into a graph-based workflow. A task graph allows selective retries and better decision-making.

A modern workflow can be modeled as:

- task nodes: research, architecture, coding, writing, verification,
- dependency edges: what must happen before another stage,
- decision points: continue, revise, escalate, or stop,
- validation gates: required checks before acceptance.

This makes the workflow more resilient than a brittle script that restarts everything when one small issue occurs.

## Revision strategy

The workflow should not restart from scratch after every failure. Instead, it should:

- localize the problem,
- return to the relevant stage,
- preserve already-gained context,
- revise minimal components,
- revalidate the result with focused checks.

This is especially important for thesis work, where renegotiating the whole narrative is costly and may reduce quality.

## Tool-aware execution

The system should choose tools based on the task type. For example:

- research-heavy tasks require search and retrieval tools,
- coding tasks require file editing, git, build, and test tools,
- writing tasks require document drafting and consistency checks,
- diagrams may need generator or visualization tools,
- academic tasks may benefit from structured citation and source-evidence checking.

This tool-aware behavior is a key differentiator between a prompt-only chatbot and a useful agentic pipeline.

## Human-in-the-loop checkpoints

The workflow should include review moments where a human can intervene:

- before major architectural decisions,
- when the project scope changes significantly,
- before a document is considered final,
- when verification reveals risk or uncertainty,
- when an output is scientifically or ethically sensitive.

Human intervention keeps the system aligned with the user's intent and improves trust in the final result.

## Desired operating characteristics

The workflow should be:

- observable,
- auditable,
- resumable,
- incremental,
- extensible,
- testable,
- safe under failure conditions.

## Implementation priority plan

The system should be built in a strict order of importance.

### Priority 1 - state and orchestration

- project and session model,
- task lifecycle and stage tracking,
- dependency-aware execution graph,
- memory store for requirements, notes, decisions, and logs,
- explicit run state persisted between steps.

### Priority 2 - tool execution

- repository file editing,
- git and diff operations,
- terminal and test execution,
- default validation tools,
- sandboxed or restricted tool permissions.

### Priority 3 - verification and revision

- code validation,
- document consistency checks,
- requirement tracing,
- fail-state handling,
- targeted revision loops instead of full restarts.

### Priority 4 - knowledge and retrieval

- PostgreSQL memory persistence,
- pgvector or similar retrieval layer,
- embedding-based recall for previous projects and notes,
- evidence-aware writing and research support.

### Priority 5 - multi-agent specialization

- orchestrator, researcher, coder, writer, reviewer, verifier,
- clear role boundaries,
- handoff architecture,
- human approval checkpoints for strategic decisions.

### Priority 6 - production maturity

- telemetry,
- observability,
- artifact versioning,
- queueing for async work,
- safe execution shells,
- deployment and monitoring support.

## Strategic direction

The ideal version of this project is a harness that can support multi-step, multi-agent, tool-connected project work without losing control. Instead of a single holistic agent doing everything in one pass, the system should orchestrate focused, specialized execution with strong state tracking and verification.
