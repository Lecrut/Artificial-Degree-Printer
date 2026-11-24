"""§XXIII: what the re-plan and the verdict are told — 01, 2026-11-23 (a dead environment behind a `verified`, a hung test
charged to the experiment, the metric of the last attempt lost in the history, a metric named in no interface)."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph.validate import code_violations
from adk.orchestration.common import _degenerate_metrics
from adk.orchestration.failure_attribution import _pytest_culprits
from adk.orchestration.fragment_replan import _latest_errors

_HANG = (
    "Pytest failure: Pytest: a test hung and was stopped after 20s (probably an infinite loop). Stack (newest frame first):\n"
    r'File "tests\test_figures.py", line ??? in mock_read_csv' "\n"
    r'File "tests\test_figures.py", line 53 in mock_read_csv' "\n"
    r'File "tests\test_figures.py", line 60 in test_plot'
)


def test_hung_test_is_charged_to_the_file_of_the_newest_frame():
    assert _pytest_culprits(_HANG) == [("tests/test_figures.py", False)]
    in_code = _HANG.replace(r'File "tests\test_figures.py", line ??? in mock_read_csv', 'File "figures.py", line 9 in plot')
    assert _pytest_culprits(in_code) == [("figures.py", False)]


def test_latest_errors_skip_planner_entries_and_older_attempts():
    history = [
        {"task_id": "R2_1", "issues": ["old NameError"]},
        {"task_id": "R4_1", "issues": ["Metric 'mean_td_error' declared in the plan was not measured."]},
        {"task_id": "REPLAN", "issues": ["Interface of x.py changed by the re-plan."]},
    ]
    assert _latest_errors(history) == ["Metric 'mean_td_error' declared in the plan was not measured."]
    assert _latest_errors([]) == []


def test_degenerate_metric_is_zero_without_spread_over_several_runs(tmp_path: Path):
    (tmp_path / "results.csv").write_text(
        "method,metric,value,std_dev,n_runs\n"
        "q,win_rate,0.0,0.0,3\nq,td_error,0.14,0.0,3\nq,draws,0.0,0.0,1\nq,loss,0.0,0.2,3\n",
        encoding="utf-8",
    )
    assert _degenerate_metrics(tmp_path) == [
        "Metric 'win_rate' is exactly 0 in every run (std_dev 0): the experiment measures nothing. Find the cause in "
        "the modules the experiment uses (a game that never ends, an agent that never learns, a value that is never "
        "updated) and fix it there, not by changing how the number is written."
    ]


_ENTRY = (
    '"""Runs the experiment; writes results.csv with win_rate."""\n\n\ndef run() -> None:\n    """Writes the rows."""\n    ...\n'
)


def test_every_declared_metric_is_named_in_the_entrypoint_interface():
    plan = {"run.py": _ENTRY}
    rules = {v.rule for v in code_violations(plan, "run.py:run", "", ["win_rate", "mean_td_error"])[1]}
    assert "METRIC_NOT_IN_ENTRYPOINT" in rules
    messages = [str(v) for v in code_violations(plan, "run.py:run", "", ["win_rate", "mean_td_error"])[1]]
    assert any("mean_td_error" in m for m in messages) and not any("`win_rate`" in m for m in messages)
    assert "METRIC_NOT_IN_ENTRYPOINT" not in {v.rule for v in code_violations(plan, "run.py:run", "", ["win_rate"])[1]}


_BASE_AND_NOOP = '''
class Agent:
    def act(self, obs) -> int:
        raise NotImplementedError

    def update(self, r: float) -> None:
        raise NotImplementedError


class RandomAgent(Agent):
    def act(self, obs) -> int:
        return 0

    def update(self, r: float) -> None:
        pass
'''


def test_abstract_base_methods_and_a_noop_update_are_not_stubs():
    from adk.hypergraph.oracles import stub_functions

    assert stub_functions(_BASE_AND_NOOP) == []


def test_real_stubs_stay_stubs():
    from adk.hypergraph.oracles import stub_functions

    only_stubs = _BASE_AND_NOOP.replace("return 0", "raise NotImplementedError")
    assert stub_functions(only_stubs) == ["RandomAgent.act", "RandomAgent.update"]
    assert stub_functions("class A:\n    def f(self) -> None:\n        pass\n    def g(self) -> int:\n        ...\n") == ["A.f", "A.g"]
    assert stub_functions("class A:\n    def f(self) -> None:\n        pass\n    def g(self) -> int:\n        return 1\n") == []
    assert stub_functions("def f() -> None:\n    pass\n") == ["f"]
