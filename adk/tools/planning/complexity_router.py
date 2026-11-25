from __future__ import annotations

from adk.core.models import ModelTier

# The small model does the work. The large one takes over a vertex after the small model failed it this many
# times (failed verifications and rejected answers, counted on the vertex in H over all its tasks; §XI B4).
ESCALATE_TO_LRM_AFTER = 2
# A thesis chapter, the research and the bibliography fail on a pointer the harness words with the list of what may be
# cited: the small model gets one more try than it does on code (§XXIX D6).
DOC_ESCALATE_TO_LRM_AFTER = 3
# A mechanical failure (a lint rule, a syntax or an import error) names its own fix: the small model keeps it longer.
MECHANICAL_ESCALATE_TO_LRM_AFTER = 4
DOCUMENT_KINDS = ("chapter", "research", "bib")


def select_model_tier(failures: int = 0, *, kind: str | None = None, mechanical: bool = False, remediation: bool = False) -> ModelTier:
    """Tier for a build attempt: 'SML' by default, 'LRM' once the small model has failed `failures` times.

    `kind` is the kind of the vertex in H (documents escalate later than code), `mechanical` says that every finding
    of the failure names its own fix, `remediation` that the repair planner is asking: it decides what to change, in the
    task repairs (after the fast repairs of the author) and in the defense of Gate 3 alike, so it is the large model's.

    Until 2026-11-14 the tier followed the node (`degree >= 2 or weight > 1.5`), which in any project with code,
    tests and a thesis meant LRM for almost every task and, after the weight escalation, for the rest of the run:
    83% of the 2026-11-13 run's model time went to the large model."""
    failures = int(failures)
    if remediation:
        return "LRM"
    if mechanical:
        return "LRM" if failures >= MECHANICAL_ESCALATE_TO_LRM_AFTER else "SML"
    limit = DOC_ESCALATE_TO_LRM_AFTER if kind in DOCUMENT_KINDS else ESCALATE_TO_LRM_AFTER
    return "LRM" if failures >= limit else "SML"


def select_planning_tier(agent: str, *, attempt: int = 1, has_feedback: bool = False) -> ModelTier:
    """Tier for a planning call. Only the first answer of a module author is the small model's: the outline it builds on
    is decided and so are the interfaces it depends on. Every correction, every critic and every decision about the
    architecture is the large model's (§XXIX D6)."""
    return "SML" if agent == "plan_module" and attempt == 1 and not has_feedback else "LRM"
