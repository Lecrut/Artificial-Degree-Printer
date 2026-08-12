# Verification and Quality Control

## Verification goals

The system must confirm that generated work is correct, useful, and aligned with the goal.

## Examples of checks

- unit tests,
- integration tests,
- formatting or lint checks,
- type checking,
- consistency checks between code and documentation,
- thesis/article structure validation,
- figure and caption consistency checks,
- quality metrics and review criteria.

## Validation principle

Each workflow stage should have at least one lightweight validation path. If a validation fails, the system should return to the appropriate stage rather than continuing blindly.

## Output acceptance

A result is acceptable when:

- it satisfies the request,
- it passes relevant automated checks,
- it remains consistent with the project state,
- it can be traced to requirements or feedback.
