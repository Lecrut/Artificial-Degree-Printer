# Pipeline

This folder describes the whole system as a simple chain or graph of tasks.

## Proposed stages

1. intake - gather requirements and context,
2. plan - break the work into tasks,
3. retrieve - select knowledge, files, and source material,
4. generate - create or modify code and text,
5. verify - tests, validation, and metrics,
6. revise - fixes after feedback or failures,
7. publish - save the report, logs, and results.

## Implementation note

A simple linear flow with a return to generate or revise is enough at the beginning. Later this can be expanded into a task graph with transition conditions.