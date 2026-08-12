# Artificial Degree Printer

This repository is a scaffold for a system that automates the creation and modification of software projects, project documentation, thesis content, and scientific article text using AI.

## Project goal

The main objective is to build a semi-autonomous workflow that:
- receives user requirements and feedback,
- plans the work into stages,
- generates or updates code and text,
- validates the result with tests and structured checks,
- stores state, decisions, and execution logs,
- revises the output when requirements or review comments change.

## Project scope

The system targets computer science projects, academic theses, and scientific articles. It is designed to support the practical part, source code, documentation, and research writing with AI-driven assistance.

## Documentation

The full project description is available in [documentation/README.md](documentation/README.md).

## Repository structure

- [adk/](adk/) - agent scaffolding, prompts, memory, and workflow notes
- [adk/prompts/](adk/prompts/) - pipeline prompts
- [adk/pipeline/](adk/pipeline/) - workflow description
- [adk/verification/](adk/verification/) - validation rules
- [adk/memory/](adk/memory/) - session state and working memory
- [adk/logs/](adk/logs/) - execution logs
- [adk/assets/](adk/assets/) - diagrams, figures, and provenance metadata

## Minimal run

```bash
python main.py "Stwórz prosty system do automatyzacji pracy dyplomowej"
```

The script stores the current state in [adk/memory/session.json](adk/memory/session.json) and logs execution in [adk/logs/](adk/logs/).

## AI-oriented principles

This project is intended to be understandable to both humans and AI agents. The main design principles are:

- modular prompts,
- explicit task stages,
- persistent state and memory,
- verification before accepting results,
- traceable changes and logged execution,
- consistent alignment between code, documentation, and visuals.

## Status

This is a structured starter repository for building the full system described in the project documentation. The next steps may include real prompt implementations, automatic validation, and a stronger execution engine.