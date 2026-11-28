"""Evolution after the planning critics (§XVIII): a blocking finding is a failure of the agent that wrote the part.

The critics (`outline_critic_guard`, `module_critic_guard`, `plan_critic_guard`) are the best source of what the
planners do wrong, but their findings used to be spent on one correction and forgotten. Each blocker is now logged as
a failure of its author (`plan_outline` / `plan_module`) in the ledger's `category_log` (the data the consolidation
uses to drop a rule that did not make its failures rarer). When the same author has been blocked in at least two
different places since its last rule, the Evolution Architect is called for it and its rule is written into the
author's prompt, which every later planning call reads: the next module already benefits, and the planner keeps
learning as long as the critics keep finding new patterns."""

from __future__ import annotations

from adk.orchestration.common import _fit_items

CRITIC_CATEGORY = "critic"
CRITIC_PATTERN_MIN = 2  # different places (modules / outline rounds) blocked for one author


class PlanEvolutionMixin:
    """Part of NeuroSymbolicOrchestrator; relies on `_critic_log` and `_critic_cursor` set in its __init__."""

    def _learn_from_critic(self, agent: str, target: str, findings: list[str]) -> None:
        """Log blocking `findings` against `agent` (about `target`); on a pattern, evolve that agent."""
        if not findings:
            return
        self._critic_log.append({"agent": agent, "target": target, "findings": findings})
        self._log_failure_category(len(self._critic_log), agent, CRITIC_CATEGORY, target)
        # Only evidence newer than the agent's last evolution counts: a pattern is again two new places, so the
        # planner keeps learning through the run, but one blocked place never writes a rule.
        fresh = [e for e in self._critic_log[self._critic_cursor.get(agent, 0):] if e["agent"] == agent]
        targets = sorted({e["target"] for e in fresh})
        if not self.enable_layer4 or len(targets) < CRITIC_PATTERN_MIN:
            return
        self._critic_cursor[agent] = len(self._critic_log)
        print(f"  [WARSTWA 4: KRYTYK PLANU -> EWOLUCJA] {agent}: blokady w {len(targets)} nowych miejscach, uruchamiam Architekta...", flush=True)
        examples = _fit_items([f for e in fresh for f in e["findings"]][:3])
        self._run_evolution_step({
            "pattern": {"category": CRITIC_CATEGORY, "occurrences": len(targets), "tasks": targets, "examples": examples},
            "failed_agent": agent,
            "agent_failure_count": sum(1 for e in self._critic_log if e["agent"] == agent),
            "cycle_index": len(self._critic_log),
            "source": "planning_critic",
        })
