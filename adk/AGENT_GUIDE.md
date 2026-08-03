# ADK Agent Guide

This document explains how an agent should interpret this scaffold.

## Expected workflow

1. Read the task description.
2. Derive structured requirements.
3. Select the relevant prompt file.
4. Produce a plan before editing files.
5. Keep code changes small and local.
6. Save state and log the run.
7. Verify the output before continuing.

## File responsibilities

- `main.py` - entry point for the minimal runnable program,
- `adk/state.py` - typed task state,
- `adk/memory_store.py` - state persistence,
- `adk/logger.py` - execution log storage,
- `adk/prompt_catalog.py` - prompt discovery,
- `adk/prompts/` - prompt templates,
- `adk/pipeline/` - workflow design notes,
- `adk/verification/` - validation rules,
- `adk/assets/` - figure and diagram provenance,
- `adk/memory/` - session memory artifacts,
- `adk/logs/` - execution logs.

## Editing rule

Prefer one small change at a time. If a validation step fails, fix the same slice before widening the scope.