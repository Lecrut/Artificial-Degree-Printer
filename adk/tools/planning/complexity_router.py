from __future__ import annotations

from adk.core.models import ModelTier

# The small model does the work. The large one takes over a vertex after the small model failed it this many
# times (failed verifications and rejected answers, counted on the vertex in H over all its tasks; §XI B4).
ESCALATE_TO_LRM_AFTER = 2


def select_model_tier(failures: int = 0) -> ModelTier:
    """Tier for a build attempt: 'SML' by default, 'LRM' once the small model has failed `failures` times.

    Until 2026-11-14 the tier followed the node (`degree >= 2 or weight > 1.5`), which in any project with code,
    tests and a thesis meant LRM for almost every task and, after the weight escalation, for the rest of the run:
    83% of the 2026-11-13 run's model time went to the large model."""
    return "LRM" if int(failures) >= ESCALATE_TO_LRM_AFTER else "SML"
