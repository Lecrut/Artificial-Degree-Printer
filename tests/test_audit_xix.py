"""§XIX (2026-11-22): the plan carries no executable examples. Behaviour is described in the docstrings in words; the
plan is not checked against examples, σ keeps no `behaviour`, and no prompt asks for `>>>`."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph import code_violations
from adk.hypergraph.build import spec_from_stub
from tests.test_audit_vi import _ENTRY, _GOOD

_WRONG_EXAMPLE = (
    "\n\ndef extra() -> int:\n"
    '    """Never raises.\n\n'
    "    >>> ns = (0,) * 9; ns[0] = 1\n"
    "    >>> extra() + 0.5\n"
    "    999\n"
    '    """\n'
    "    ...\n"
)
_PROMPTS = Path(__file__).resolve().parent.parent / "adk" / "agents"


def test_a_wrong_example_in_a_docstring_does_not_reject_the_plan() -> None:
    """Before: an impossible doctest was DOCTEST_INVALID_ON_STUBS and cost rounds of planning (21 of 30 failed
    verdicts in 02, 2026-11-21). Now a docstring is prose, whatever it contains."""
    plan = {**_GOOD, "src/data_generator.py": _GOOD["src/data_generator.py"] + _WRONG_EXAMPLE}
    assert code_violations(plan, _ENTRY)[1] == []


def test_the_specification_of_a_module_has_no_executable_examples() -> None:
    spec = spec_from_stub("src/data_generator.py", _GOOD["src/data_generator.py"] + _WRONG_EXAMPLE, {})
    assert "behaviour" not in spec and {"import", "symbols", "uses", "packages"} <= set(spec)


def test_no_prompt_asks_for_executable_examples() -> None:
    for name in ("planning/plan_critic_guard.md", "planning/module_critic_guard.md", "planning/plan_change_guard.md",
                 "building/seed_coder.md", "building/seed_tester.md"):
        assert "doctest" not in (_PROMPTS / name).read_text(encoding="utf-8").lower(), name
    for name in ("planning/plan_module.md", "planning/task_planner.md"):
        text = (_PROMPTS / name).read_text(encoding="utf-8")
        assert "no executable examples" in text and "Doctests" not in text, name
