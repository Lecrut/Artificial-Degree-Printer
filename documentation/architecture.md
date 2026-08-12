# Architecture

## High-level structure

The system is organized as a modular pipeline with several layers:

1. Input layer
   - user requests
   - project requirements
   - feedback and review comments

2. Planning layer
   - decomposition of work into tasks
   - tool and prompt selection
   - stage ordering

3. Knowledge and context layer
   - prompt catalog
   - session memory
   - working state
   - project references

4. Execution layer
   - code generation
   - document generation
   - asset creation
   - workflow orchestration

5. Verification layer
   - tests
   - validation checks
   - consistency checks
   - reporting

6. Correction layer
   - issues handling
   - iterative improvement
   - revision loops

## Key design principles

- modularity,
- explicit state management,
- traceable execution,
- verifiable outputs,
- prompt-driven orchestration,
- iterative revision based on feedback.

## Main components

### Prompt layer
Prompt templates define how each stage of the pipeline should behave. They should be modular and reusable across tasks.

### Memory layer
The system stores:

- current task state,
- relevant requirements,
- notes and decisions,
- logs from prior executions.

### Execution layer
This layer performs generation or modification of:

- source code,
- documentation,
- thesis/article text,
- diagrams or figures.

### Validation layer
This layer checks whether generated content meets project requirements and quality standards. It can include unit tests, consistency checks, and review criteria.

## Example flow

1. User provides requirements.
2. The system analyzes the task and prepares a plan.
3. The pipeline selects relevant prompts and tools.
4. Code and text are generated or updated.
5. Verification is performed.
6. The system revises the output if needed.
7. Results and logs are saved.
