# Verification

This folder stores rules for checking whether the output is correct.

## What can be checked

- unit tests,
- integration tests,
- lint,
- type checking,
- consistency between the text and the plan,
- consistency between figures and their descriptions,
- quality metrics, if the project uses them.

## Idea

Each generation stage should have at least one cheap and fast verification. If validation fails, the system should return only to the nearest responsible stage.