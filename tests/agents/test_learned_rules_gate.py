"""Learned rules (Layer 4): a rule describes a way of working and not an incident, a pattern across tasks is needed, rules are deduplicated, fit the budget and are dropped when their category did not get rarer."""

from __future__ import annotations

from pathlib import Path

from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.evolution.agent_mutator import (
    _effective_rules,
    _fit_invariants,
    rule_rejection_reason,
)
from tests.support.adk_sandbox import _clone_adk_env
from tests.support.run_loop_fixtures import _evolution_with_decision

GOOD = (
    "When you use a symbol from another module, take its name and signature from the contract in the payload, "
    "because the contract is the only source of truth about neighbours."
)


def test_rules_from_the_2026_11_13_run_are_rejected() -> None:
    names = {"tictoc_game.py", "tictoc_game", "TicTacToeGame"}
    assert rule_rejection_reason("Never import TicTacToeGame from tictoc_game directly.", names, [])
    assert rule_rejection_reason("Avoid F821 by defining names before use.", names, [])
    assert rule_rejection_reason("Ensure triple-quoted docstrings are closed before code.", names, [])
    assert rule_rejection_reason("Use sys.path manipulation so imports resolve.", names, [])


def test_a_way_of_working_passes_but_its_near_copy_does_not() -> None:
    assert rule_rejection_reason(GOOD, {"tictoc_game"}, []) is None
    near_copy = GOOD.replace("take its name", "always take the name")
    assert "repeats" in str(rule_rejection_reason(near_copy, set(), [GOOD]))


def test_plain_words_are_not_project_identifiers() -> None:
    """§VI.9 P3: a module named model.py or agent.py must not ban the words "model"/"agent" from rules."""
    from adk.orchestration.evolution.evolution import _looks_like_identifier

    assert not _looks_like_identifier("model") and not _looks_like_identifier("Agent")
    assert all(_looks_like_identifier(n) for n in ("q_learner", "TicTacToeGame", "game.py", "env2", "MAX_STEPS"))
    rule = "When a model module exposes an agent, keep its public API stable, because tests are written against it."
    assert rule_rejection_reason(rule, {n for n in ("model", "agent", "q_learner") if _looks_like_identifier(n)}, []) is None


def test_invariants_are_deduplicated_and_fit_the_budget() -> None:
    fitted = _fit_invariants([GOOD, GOOD + " ", *[f"When case {i} happens, do thing {i}, because reason {i}." for i in range(10)]])
    assert len(fitted) <= 6 and sum(map(len, fitted)) <= 1200
    assert len({f.strip() for f in fitted}) == len(fitted)


def test_a_rule_whose_category_did_not_get_rarer_is_dropped() -> None:
    ledger = {
        "rules": [
            {"agent": "seed_coder", "rule": "useless", "category": "pytest:AssertionError", "cycle": 2},
            {"agent": "seed_coder", "rule": "useful", "category": "F821", "cycle": 2},
        ],
        "category_log": [
            {"agent": "seed_coder", "category": "pytest:AssertionError", "cycle": c} for c in (1, 2, 3, 4, 5, 6)
        ] + [{"agent": "seed_coder", "category": "F821", "cycle": c} for c in (1, 2)],
    }
    kept, dropped = _effective_rules(["useless", "useful"], ledger, "seed_coder")
    assert kept == ["useful"]
    assert [d["rule"] for d in dropped] == ["useless"]


def test_evolution_waits_for_a_pattern_across_tasks(tmp_path: Path):
    """One task failing three times is an incident: a fast fix by the file's author (the identical error after it
    ends the fast fixes, §XIV Q3), one planner cycle, no evolution. The same category of failure in a second task is a pattern: the architect runs once, with the
    examples of both tasks, and the task gets no more than its one planner cycle (Audit IV §IV.7 pkt 6, §IV.6.3 A)."""
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=False, provider="mock")

    real_verify = orch._run_verification_step
    real_evolve = orch._run_evolution_step
    verifications: dict[str, int] = {}
    evolutions: list[dict] = []

    def failing_three_times_per_task(task, *args, **kwargs):
        t_id = str(task.get("task_id"))
        verifications[t_id] = n = verifications.get(t_id, 0) + 1
        if n <= 3:
            return {
                "status": "FAIL",
                "failed_task_id": t_id,
                "failed_node": task.get("target_node"),
                "failed_file": "config.py",
                "failed_agent": "seed_coder",
                # Differing timings must not make it look like a new failure.
                "supervisors": {"code_auditor": {"status": "FAIL", "issues": [
                    f"Pytest failure: FAILED test_core.py::test_value - AssertionError (0.{n}s)"
                ]}},
                "summary": "Layer 3 verification failed.",
            }
        return real_verify(task, *args, **kwargs)

    def recording_evolve(payload, *args, **kwargs):
        evolutions.append(payload)
        return real_evolve(payload, *args, **kwargs)

    orch._run_verification_step = failing_three_times_per_task
    orch._run_evolution_step = recording_evolve

    res = orch.run("Zbuduj moduł walidacji parametrów")

    actions = [c["w4_action"] for c in res.get("architecture_cycles", [])]
    # §XXVII: every task gets both author repairs (no `Q3` shortcut for a vertex of H); the first one's pattern is
    # still one task, so no evolution.
    assert actions[:3] == ["FAST_FIX", "FAST_FIX", "SKIPPED_NO_PATTERN"]
    # The sixth cycle is the architect's own decision (the mock splits an agent with many failures); the third
    # task repeats the same category and gets no second rule.
    assert not actions[5].startswith("SKIPPED")
    assert len(evolutions) == 1
    pattern = evolutions[0]["pattern"]
    assert pattern["category"] == "pytest:AssertionError" and pattern["occurrences"] == 2
    assert len(pattern["examples"]) == 2
    # The architect reads the pattern, not the whole report.
    assert len(evolutions[0]["validation_report"]["issues"]) <= 3


def test_rule_naming_one_incident_is_not_written_into_the_prompt(tmp_path: Path):
    orch, res = _evolution_with_decision(
        tmp_path, {"action": "MUTATE_AGENT", "agent_id": "seed_coder", "rule": "Unikaj niezgodności w zadaniu T1 na węźle v1."}
    )
    assert res["action"] == "MUTATION_SKIPPED"
    coder = (orch.agents_dir / "building" / "seed_coder.md").read_text(encoding="utf-8")
    assert "zadaniu T1" not in coder


def test_missing_rule_does_not_inject_a_filler(tmp_path: Path):
    _orch, res = _evolution_with_decision(tmp_path, {"action": "MUTATE_AGENT", "agent_id": "seed_coder"})
    assert res["action"] == "MUTATION_SKIPPED"
