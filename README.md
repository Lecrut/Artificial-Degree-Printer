# Artificial Degree Printer

This repository is a minimal scaffold for a system that automates the creation and modification of software projects, documentation, and thesis or paper content.

At this stage the repository contains only the organizational skeleton:
- prompt files for each stage of the workflow,
- pipeline documentation,
- verification placeholders,
- memory and log storage.

## Purpose

The system is meant to operate in a semi-autonomous mode:
1. the user provides requirements and feedback,
2. the pipeline plans the work,
3. the models generate or modify code and text,
4. tools run tests and validation,
5. the system records results, logs the run, and suggests the next iteration.

## Proposed layout

- `adk/prompts/` - prompts for each stage,
- `adk/pipeline/` - stage flow and control logic,
- `adk/verification/` - quality checks and metrics,
- `adk/memory/` - working state, decisions, and context memory,
- `adk/logs/` - execution logs,
- `adk/assets/` - generated or external figures and their provenance.

## How to use it

Treat this scaffold as a project notebook. In the next steps you can add:
- real prompts,
- a task state schema,
- tool definitions,
- report formats and validation checklists.

## Run

The minimal program starts from `main.py`:

```bash
C:/Users/Filip/AppData/Local/Programs/Python/Python313/python.exe main.py "Stwórz prosty system do automatyzacji pracy dyplomowej"
```

The program writes the current state to `adk/memory/session.json` and the execution log to `adk/logs/`.