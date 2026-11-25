"""Guards against a false `verified`: a test without assertions, a function that promises a value and never returns, stubs that are not stubs, degenerate and unmeasured metrics."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph.oracles import (
    assertionless_tests,
    functions_without_return,
    static_defects,
)
from adk.hypergraph.validate import code_violations
from adk.orchestration.common import _degenerate_metrics
from tests.support.failed_vertex_project import _planned

_ENTRY = (
    '"""Runs the experiment; writes results.csv with win_rate."""\n\n\ndef run() -> None:\n    """Writes the rows."""\n    ...\n'
)


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


def test_only_an_unmeasured_declared_metric_blocks(tmp_path: Path) -> None:
    """K6: a measured but undeclared metric blocked the final gate although documented as non-blocking; `F1` ≠ `f1`."""
    from adk.orchestration import agent_texts as texts
    from adk.orchestration.common import _declared_vs_measured_metrics

    (tmp_path / "results.csv").write_text("method,metric,value\na,f1,1\na,auc,1\n", encoding="utf-8")
    findings = _declared_vs_measured_metrics(["F1", "recall"], tmp_path)
    assert texts.metric_not_measured("F1") not in findings
    assert texts.metric_not_measured("recall") in findings and texts.metric_not_declared("auc") in findings


def test_declared_metrics_are_compared_with_what_was_measured(tmp_path: Path):
    from adk.orchestrator import _declared_vs_measured_metrics

    (tmp_path / "results.csv").write_text(
        "method,metric,value\nproposed,win_rate,0.6\nproposed,episode_length,7\n", encoding="utf-8"
    )
    findings = _declared_vs_measured_metrics(["win_rate", "draw_rate"], tmp_path)
    assert any("'draw_rate'" in f and "was not measured" in f for f in findings)
    assert any("'episode_length'" in f and "not declared" in f for f in findings)
    assert not any("'win_rate'" in f for f in findings)
    # Before the experiment has run there is nothing to compare yet.
    assert _declared_vs_measured_metrics(["win_rate"], tmp_path / "empty") == []


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


def test_every_declared_metric_is_named_in_the_entrypoint_interface():
    plan = {"run.py": _ENTRY}
    rules = {v.rule for v in code_violations(plan, "run.py:run", "", ["win_rate", "mean_td_error"])[1]}
    assert "METRIC_NOT_IN_ENTRYPOINT" in rules
    messages = [str(v) for v in code_violations(plan, "run.py:run", "", ["win_rate", "mean_td_error"])[1]]
    assert any("mean_td_error" in m for m in messages) and not any("`win_rate`" in m for m in messages)
    assert "METRIC_NOT_IN_ENTRYPOINT" not in {v.rule for v in code_violations(plan, "run.py:run", "", ["win_rate"])[1]}


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


def test_a_test_of_comments_only_checks_nothing():
    src = "def test_a():\n    x = 1\n    # assert x\n\ndef test_b():\n    assert 1\n"
    assert assertionless_tests(src) == ["test_a"]


def test_every_kind_of_check_counts_as_an_assertion():
    src = (
        "import pytest\nimport numpy as np\n\n"
        "def _check(v):\n    assert v\n\n"
        "def test_raises():\n    with pytest.raises(ValueError):\n        int('x')\n\n"
        "def test_approx():\n    pytest.approx(1.0)\n\n"
        "def test_numpy():\n    np.testing.assert_allclose(1, 1)\n\n"
        "def test_helper():\n    _check(1)\n\n"
        "class TestK:\n    def test_m(self):\n        self.assertEqual(1, 1)\n"
    )
    assert assertionless_tests(src) == []


def test_a_nested_function_does_not_make_a_test_check_something():
    assert assertionless_tests("def test_a():\n    def inner():\n        assert 1\n") == ["test_a"]


def test_a_function_promising_a_value_without_return_is_found():
    src = "def f(n: int) -> int:\n    for _ in range(n):\n        pass\n"
    assert functions_without_return(src) == ["f"]


def test_functions_that_legitimately_have_no_return_value_pass():
    src = (
        "from abc import abstractmethod\nfrom typing import Iterator, NoReturn\n\n"
        "def none() -> None:\n    x = 1\n\n"
        "def untyped(n):\n    x = n\n\n"
        "def gen() -> Iterator[int]:\n    yield 1\n\n"
        "def fails() -> int:\n    x = 1\n    raise ValueError(x)\n\n"
        "def never() -> NoReturn:\n    x = 1\n\n"
        "def stub() -> int:\n    ...\n\n"
        "def nested() -> int:\n    def inner() -> int:\n        return 1\n    return inner()\n\n"
        "class A:\n    @abstractmethod\n    def m(self) -> int:\n        x = 1\n\n"
        "    def n(self) -> int:\n        return 2\n"
    )
    assert functions_without_return(src) == []


def test_a_return_only_in_a_nested_function_does_not_count():
    src = "def f() -> int:\n    def inner() -> int:\n        return 1\n    inner()\n"
    assert functions_without_return(src) == ["f"]


def test_static_defects_judge_by_the_kind_of_the_vertex(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "tests").mkdir()
    (orch.workspace_dir / "tests/test_core.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    (orch.workspace_dir / "config.py").write_text("def f() -> int:\n    x = 1\n", encoding="utf-8")
    assert [v.rule for v in static_defects(orch.workspace_dir, "tests/test_core.py", h)] == ["TEST_NO_ASSERTIONS"]
    assert [v.rule for v in static_defects(orch.workspace_dir, "config.py", h)] == ["FUNCTION_NEVER_RETURNS"]
    assert static_defects(orch.workspace_dir, "unplanned.py", h) == []


def test_static_defects_ignore_a_file_that_does_not_parse(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "config.py").write_text("def f(:\n", encoding="utf-8")
    assert static_defects(orch.workspace_dir, "config.py", h) == []
