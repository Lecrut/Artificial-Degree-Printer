# System state

This file should describe what data the system keeps between steps.

## Minimal fields

- request - the user task description,
- requirements - structured requirements,
- plan - the list of steps to execute,
- context - extracted context from the repo or sources,
- changes - the list of executed changes,
- verification - test and validation results,
- notes - notes for the next iteration.

## Notes

The state should stay simple, serializable, and readable for the next pipeline stage.