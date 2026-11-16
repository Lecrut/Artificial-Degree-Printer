"""Stage 2 of Audit IV: learned rules describe a way of working (§IV.6.3 B), the learned section stays within a
budget, and a rule that did not lower its failure category is dropped (§IV.6.3 D)."""

from __future__ import annotations

from adk.orchestration import agent_texts as texts
from adk.orchestration.common import _issue_category
from adk.tools.evolution.agent_mutator import _effective_rules, _fit_invariants, rule_rejection_reason

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


def test_failure_category_ignores_the_file() -> None:
    a = ["Pytest failure: FAILED test_game.py::test_reset - AssertionError"]
    b = ["Pytest failure: FAILED test_env.py::test_step - AssertionError"]
    assert _issue_category(a) == _issue_category(b) == "pytest:AssertionError"
    assert _issue_category(["Syntax error in game.py: invalid syntax"]) == "SyntaxError"


def test_every_gate_rejection_wrapper_is_harness_not_generic_and_outweighs_quoted_errors() -> None:
    """§VI.9 P2: two of the three builder-exception wrappers fell into `generic` (2026-11-14)."""
    for wrapper in (
        texts.task_exception("T3", "n2", "a.py", texts.contract_breach(["a.py: f(x) -> f(y)"], "")),
        texts.fast_repair_exception("T3_FIX1", "a.py", texts.symbol_edits_rejected(["a.py:f: SyntaxError"])),
        texts.repair_task_exception("T3_FIX", "n2", "a.py", texts.unparsable_code(["a.py:3: invalid syntax"])),
    ):
        assert _issue_category([wrapper]) == "harness", wrapper
    assert _issue_category(["Import contract violation: env.py imports TicTacToe from game.py"]) == "contract"
    assert _issue_category(["Unresolved pointer: \\ref_ast{x.py:Y} (Source file 'x.py' does not exist)"]) == "document"


def test_plain_words_are_not_project_identifiers() -> None:
    """§VI.9 P3: a module named model.py or agent.py must not ban the words "model"/"agent" from rules."""
    from adk.orchestration.evolution import _looks_like_identifier

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
