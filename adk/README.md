# ADK sketch

This folder documents a simple file split for a system that automates project work, documentation, and thesis or paper text.

## Contents

- `prompts/` - reusable prompts for each pipeline step,
- `pipeline/` - the task sequence and where the workflow can loop back,
- `verification/` - quality rules for results,
- `memory/` - session state, decisions, and items to remember,
- `logs/` - execution records,
- `assets/` - figures, diagrams, and provenance information.

## Minimal flow

1. Collect requirements.
2. Build a plan.
3. Generate or modify code and documentation.
4. Run tests or other validators.
5. Evaluate the result.
6. If needed, return only to the problematic stage.

## Note

The files may remain partially empty at this stage. The structure matters more than the full implementation.