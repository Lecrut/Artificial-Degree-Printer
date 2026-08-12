# Workflow

## Basic execution pipeline

1. Intake
   - collect the user request and constraints
2. Analyze context
   - identify requirements, dependencies, and existing project state
3. Plan
   - split the task into stages and identify tool needs
4. Generate
   - create or update code, text, and documentation
5. Verify
   - run tests, checks, and consistency validation
6. Revise
   - fix errors or change content based on feedback
7. Save state
   - store logs, decisions, and final project state

## Revision loop

The workflow should support loops between generation and verification. If validation fails, the system should return to the most relevant stage instead of restarting the whole project blindly.

## Execution model

The project may evolve from a simple linear pipeline toward a graph-based workflow where tasks depend on each other and can be repeated selectively.

## Design goal

The workflow should minimize unnecessary human intervention while keeping the process observable and controllable.
