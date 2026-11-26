"""Whom a failure is charged to: the deepest frame in the workspace, the author of the code under test, the producer of a derived artifact, the thesis for a document finding, the module that fails the experiment."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from adk.mocks import code_fixtures as fx
from adk.mocks.scenarios import config_source
from adk.orchestration.common import _RunState
from adk.orchestration.failure_attribution import _pytest_culprits, _traceback_culprit
from adk.orchestration.findings import repair_findings
from adk.orchestration.recovery import RecoveryMixin
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.verification import test_runner
from tests.support.failed_vertex_project import _CONFIG as _CONFIG_failed_vertex_project
from tests.support.failed_vertex_project import _planned
from tests.support.orchestrator_sandbox import _orch
from tests.support.planned_projects import with_plan
from tests.support.results_pointer_workspace import _report, _workspace
from tests.support.run_loop_fixtures import _orch_with_workspace
from tests.support.sample_research_project import _EXPERIMENT_IFACE, _spec_orch
from tests.support.workspace_files import _write


def _game_with_test(tmp_path: Path, test_body: str) -> NeuroSymbolicOrchestrator:
    """game.py (coder) and its test (tester), as planned: the test is a T member of game.py's I bag in H."""
    orch = _orch(tmp_path)
    with_plan(
        orch, {"game.py": '"""Game."""\n\n\ndef size() -> int:\n    """Board size."""\n'}, None,
        [{"task_id": "T10", "target_node": "tests/test_game.py", "description": "tests", "assigned_agent": "seed_tester"}],
    )
    orch._materialize_workspace_artifact(
        "game.py", {"files": [{"filename": "game.py", "content": '"""Game."""\n\n\ndef size() -> int:\n    """Board size."""\n    return 9\n'}]},
        writer={"agent": "seed_coder", "task_id": "T5"},
    )
    orch._materialize_workspace_artifact(
        "tests/test_game.py",
        {"files": [{"filename": "tests/test_game.py", "content": "from game import size\n\n\ndef test_size() -> None:\n" + test_body}]},
        writer={"agent": "seed_tester", "task_id": "T10"},
    )
    return orch


_HANG = (
    "Pytest failure: Pytest: a test hung and was stopped after 20s (probably an infinite loop). Stack (newest frame first):\n"
    r'File "tests\test_figures.py", line ??? in mock_read_csv' "\n"
    r'File "tests\test_figures.py", line 53 in mock_read_csv' "\n"
    r'File "tests\test_figures.py", line 60 in test_plot'
)


def test_fast_repair_of_a_derived_artifact_goes_to_its_producer(tmp_path: Path) -> None:
    """Results go to the experiment, figures to the plotting module, the compiled thesis to thesis.md (from H)."""
    orch = _orch(tmp_path)
    plots = '"""Plots."""\n\n\ndef draw_figures() -> list:\n    """Paths."""\n'
    run = '"""Run."""\n\n\ndef main() -> None:\n    """Run."""\n'
    with_plan(orch, {"figures_of_runs.py": plots, "run.py": run}, "run.py:main", plots="figures_of_runs.py:draw_figures")

    assert orch._repair_target("figures/comparison.pdf") == "figures_of_runs.py"
    assert orch._repair_target("results.csv") == "run.py"
    assert orch._repair_target("thesis.compiled.md") == "thesis.md"


def test_verification_blames_the_side_that_breaks_the_specification(tmp_path: Path):
    """X5: the importer was blamed, the definition side never; σ decides."""
    orch = _spec_orch(tmp_path)
    (orch.workspace_dir / "src/experiment.py").write_text(_EXPERIMENT_IFACE.replace("SEEDS", "SEED_VALUE"), encoding="utf-8")
    report = orch._run_verification_step({"task_id": "T9", "target_node": "src/experiment.py"})
    assert report["status"] == "FAIL" and report["failed_file"] == "src/experiment.py"
    assert any("IMPORT_OUTSIDE_SPEC" in str(i) for i in report.get("issues", []) + report.get("errors", []) + [report])


def test_with_a_known_culprit_the_remediation_planner_is_skipped(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    orch.enable_layer4 = False
    calls: list[str] = []
    orch._execute_builder_step = lambda task, **_kw: calls.append(task["task_id"])
    orch._repair_cycle = lambda *_a, **_k: calls.append("PLANNER") or []
    failing = {"status": "FAIL", "failed_file": "src/config.py", "failed_agent": "seed_coder",
               "issues": ["API_MISSING [src/config.py]: lacks SEEDS"], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {"task_id": "T2", "target_node": "src/config.py", "description": "config", "assigned_agent": "seed_coder"}
    state = _RunState(user_prompt="p", max_retries=3, multi_cycle_waves=True, tasks=[task])
    report, stop = orch._repair_task(state, task, dict(failing), "src/config.py", "src/config.py")
    assert stop is None and report["status"] == "FAIL"
    # A breach of σ keeps both fast attempts (the planner may judge the interface between them, §XIX); no remediation planner.
    assert calls == ["T2_FIX1", "T2_FIX2"]


def test_a_pytest_failure_points_at_the_deepest_frame_in_the_workspace(tmp_path: Path):
    (tmp_path / "config.py").write_text(_CONFIG_failed_vertex_project, encoding="utf-8")
    issue = (
        "Pytest failure: F\n___ test_dir ___\ntests/test_config.py:4: in test_dir\n    get_results_dir()\n"
        "config.py:12: in get_results_dir\n    return self.output_path\nE   NameError: name 'self' is not defined\n=== 1 failed ==="
    )
    [f] = repair_findings([issue], tmp_path)
    assert f.symbol == "get_results_dir" and f.text == "test_dir: NameError: name 'self' is not defined"


def test_a_failed_run_is_charged_to_the_deepest_workspace_frame(tmp_path: Path) -> None:
    """E1: plots.py raised and three repairs rewrote the correct entrypoint."""
    ws = tmp_path / "ws"
    trace = (
        "Traceback (most recent call last):\n"
        '  File "<string>", line 59, in <module>\n'
        f'  File "{ws / "src" / "experiment.py"}", line 3, in run\n'
        f'  File "{ws / "src" / "plots.py"}", line 20, in plot_results\n'
        '  File "C:\\venv\\Lib\\site-packages\\matplotlib\\axes.py", line 9, in boxplot\n'
        "TypeError: unexpected keyword argument 'labels'"
    )
    assert _traceback_culprit(trace, ws) == "src/plots.py"
    assert _traceback_culprit("no traceback here", ws) is None


def test_the_defense_blames_the_thesis_for_a_document_finding_not_the_last_code_task(tmp_path: Path) -> None:
    orch, _h = _planned(tmp_path)
    orch.include_docs = True
    (orch.workspace_dir / "config.py").write_text(config_source(fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    (orch.workspace_dir / "thesis.md").write_text("# Praca\n\nWynik: \\ref_csv{no_such_file.csv}\n", encoding="utf-8")
    # As in 01: the model code auditor calls the code a FAIL (an opinion: it becomes a warning, not an error).
    answers = {"code_auditor.md": {"status": "FAIL", "issues": ["environment.py: invalid syntax"]}}
    orch._call_agent = lambda md, *_a, **_k: {"status": "ok", "output": dict(answers.get(Path(md).name, {"status": "PASS", "issues": []}))}
    report = orch._run_verification_step({"task_id": "R3_1", "target_node": "core.py"}, include_docs=True, is_final_gate=True)
    assert report["status"] == "FAIL" and report["failed_file"] == "thesis.md"
    assert "environment.py: invalid syntax" in report["warnings"]


def test_a_failed_figures_run_fails_the_task_of_the_plots_module(tmp_path: Path) -> None:
    orch, _h = _planned(tmp_path)
    orch.include_docs = False
    (orch.workspace_dir / "config.py").write_text(config_source(fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    orch._call_agent = lambda _md, *_a, **_k: {"status": "ok", "output": {"status": "PASS", "issues": []}}
    task = {"task_id": "R3_1", "target_node": "config.py"}  # the entrypoint of this plan is core.py
    orch._last_experiment_error = "Traceback (most recent call last):\n  File \"config.py\", line 3, in plots\nValueError: boom"
    assert orch._run_verification_step(task, include_docs=False)["status"] == "PASS"  # config.py is not the plots module
    blueprint = json.loads(orch.blueprint_path.read_text(encoding="utf-8"))
    orch.blueprint_path.write_text(json.dumps({**blueprint, "plots": "config.py:make_figures"}), encoding="utf-8")
    report = orch._run_verification_step(task, include_docs=False)
    assert report["status"] == "FAIL" and "boom" in json.dumps(report)


def test_pointer_findings_stay_with_the_writer_while_results_exist(tmp_path: Path):
    fixed = RecoveryMixin._pointer_fix_is_writers
    me = SimpleNamespace(workspace_dir=tmp_path)
    issues = ["Column 'q_learning+win_rate' not found in 'results.csv'"]
    assert not fixed(me, _report(issues), "experiment.py")  # no results yet: the producer may be at fault
    _workspace(tmp_path)
    assert fixed(me, _report(issues), "experiment.py")
    assert not fixed(me, _report(issues), "thesis.md")  # already the writer's
    assert not fixed(me, _report(issues + ["Unbalanced TikZ environment: 1 begin vs 0 end."]), "experiment.py")


def test_audit_routes_lint_error_to_the_file_that_failed(tmp_path: Path):
    orch = _orch_with_workspace(tmp_path, {"plot_results.py": "X = 1\n", "core.py": "Y = 1\n"})
    ws = str(orch.workspace_dir).replace("/", "\\")
    err = (
        "Ruff lint failure: F841 Local variable `plot_df` is assigned to but never used\n"
        f"  --> {ws}\\plot_results.py:17:9\n"
    )
    tasks = orch._tasks_from_audit({"pytest_status": "FAIL", "pytest_errors": [err]}, 1)
    assert [t["target_node"] for t in tasks] == ["plot_results.py"]
    node_id, node_path = orch._resolve_target_node(tasks[0]["target_node"], task=tasks[0])
    assert node_path == "plot_results.py"


def test_audit_redirects_derived_artifact_to_its_producer(tmp_path: Path):
    orch = _orch_with_workspace(
        tmp_path,
        {
            "core.py": "def run():\n    import csv\n    open('results.csv', 'w').write('a')\n",
            "results.csv": "method,metric,value\n",
        },
    )
    from tests.support.planned_projects import with_plan

    with_plan(orch, {"core.py": '"""Core."""\n\n\ndef run() -> None:\n    """Run."""\n'}, "core.py:run")
    tasks = orch._tasks_from_audit(
        {"pytest_status": "FAIL", "pytest_errors": ['File "results.csv", line 1\n  bad', "FAILED results.py"]}, 1
    )
    targets = {t["target_node"] for t in tasks}
    assert "results.csv" not in targets


def test_import_failure_caused_by_a_sibling_is_not_this_files_error(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    _write(ws, "src/__init__.py", "from . import env\n")
    _write(ws, "src/env.py", "def broken(:\n")
    _write(ws, "src/learner.py", "X = 1\n")

    res = test_runner.run_isolated_tests(ws, verification_dir=tmp_path / "none", scope={"files": ["src/learner.py"], "tests": []})

    assert res["status"] == "PASS", res["errors"]
    assert any("src/env.py" in note for note in res["out_of_scope"])


def test_a_wrong_result_goes_to_the_author_of_the_code_under_test(tmp_path: Path) -> None:
    """2026-11-14: a failed assertion was charged to the test file (named first by pytest); 77 repairs went to
    the tester while the bug was in the module. The module under test is read from H (the test's I bag)."""
    orch = _game_with_test(tmp_path, "    assert size() == 10\n")

    report = orch._run_verification_step(
        {"task_id": "T10", "target_node": "tests/test_game.py", "assigned_agent": "seed_tester"}, include_docs=False
    )

    assert report["status"] == "FAIL"
    assert report["failed_file"] == "game.py"
    assert report["failed_agent"] == "seed_coder"


def test_a_test_misusing_the_api_is_returned_to_the_tester_at_once(tmp_path: Path) -> None:
    """A test that calls the planned API wrongly never reaches the coder's verification: run on the stubs it fails
    for a reason of its own, and the write goes back to the tester (Φ_I.4)."""
    import pytest

    from adk.orchestration.common import MaterializationError

    with pytest.raises(MaterializationError, match="TEST_INVALID_ON_STUBS"):
        _game_with_test(tmp_path, "    assert size(3) == 9\n")


def test_explicit_path_never_routes_to_a_file_whose_name_merely_contains_it(tmp_path: Path) -> None:
    """2026-11-13: T4 on `tictoc_config.py` was sent to `config.py` by a substring match in the description."""
    import pytest

    orch = _orch(tmp_path)
    with_plan(orch, {"config.py": '"""Config."""\nSEED: int = 1\n'})

    assert orch._resolve_target_node(
        "tictoc_config.py", task={"description": "Moduł konfiguracji `tictoc_config.py` z klasą Config"}
    ) == ("tictoc_config.py", "tictoc_config.py")
    # A label that is not a path, whose description names no planned file: an error, never `config.py`.
    with pytest.raises(ValueError):
        orch._resolve_target_node("v9", task={"description": "Uzupełnij tictoc_config.py."})


def test_hung_test_is_charged_to_the_file_of_the_newest_frame():
    assert _pytest_culprits(_HANG) == [("tests/test_figures.py", False)]
    in_code = _HANG.replace(r'File "tests\test_figures.py", line ??? in mock_read_csv', 'File "figures.py", line 9 in plot')
    assert _pytest_culprits(in_code) == [("figures.py", False)]


_TEST_ONLY = (
    "Pytest failure:\n_____ test_learn _____\ntests/test_agent.py:41: in test_learn\n    assert s in [tuple(x) for x in q]\n"
    "E   {exc}\n"
)


def test_an_exception_raised_in_the_test_frame_alone_is_the_tests_unless_it_is_a_failed_assertion():
    """§XXX P6, 01 of 2026-11-25: `state1 in [tuple(s) ...]` raised `ValueError` in the test and six repairs of the
    correct module followed. Only a failed assertion (`E   assert a == b`) or `Failed` is a wrong result of the code."""
    for exc in ("ValueError: The truth value of an array is ambiguous", "IndexError: index 2 is out of bounds", "KeyError: 3"):
        assert _pytest_culprits(_TEST_ONLY.format(exc=exc)) == [("tests/test_agent.py", False)], exc
    for exc in ("assert 9 == 10", "AssertionError: wrong", "Failed: DID NOT RAISE"):
        assert _pytest_culprits(_TEST_ONLY.format(exc=exc)) == [("tests/test_agent.py", True)], exc
    in_code = _TEST_ONLY.format(exc="IndexError: index 2 is out of bounds").replace(
        "E   Index", "agent.py:42: in act\n    q[i]\nE   Index"
    )
    assert _pytest_culprits(in_code) == [("agent.py", True)]  # a frame below the test: the code raised


def _pair(module_state: str, history: list[dict], test_state: str = "written") -> SimpleNamespace:
    mod = SimpleNamespace(state=module_state, history=history)
    return SimpleNamespace(
        vertices={"agent.py": mod, "tests/test_agent.py": SimpleNamespace(state=test_state, history=[])},
        owner_of=lambda rel: rel,
    )


def _failure(version: str, exc: str = "IndexError: index 2 is out of bounds for axis 0 with size 2") -> dict:
    return {"task_id": "R1_2", "version": version, "issues": [
        f"Pytest failure:\ntests/test_agent.py:35: in test_act\nagent.py:42: in act\nE   {exc}"
    ]}


def test_a_test_is_suspect_when_its_error_survives_two_versions_of_a_module_that_never_passed():
    from adk.orchestration.failure_attribution import _suspect_test

    assert _suspect_test(_pair("failed", [_failure("a1"), _failure("b2")]), "agent.py", "tests/test_agent.py")
    assert not _suspect_test(_pair("failed", [_failure("a1"), _failure("a1")]), "agent.py", "tests/test_agent.py")  # same code twice: not a rewrite
    assert not _suspect_test(_pair("failed", [_failure("a1"), _failure("b2", "KeyError: 1")]), "agent.py", "tests/test_agent.py")  # a new error each time
    assert not _suspect_test(_pair("failed", [_failure("a1")]), "agent.py", "tests/test_agent.py")
    assert not _suspect_test(_pair("failed", [_failure("a1"), _failure("b2")], "verified"), "agent.py", "tests/test_agent.py")
    assert _suspect_test(_pair("verified", []), "agent.py", "tests/test_agent.py")  # the old rule (§XIV Q2) stays


def test_every_verdict_remembered_on_a_vertex_carries_the_version_of_its_file(tmp_path: Path) -> None:
    orch = _game_with_test(tmp_path, "    assert size() == 9\n")
    orch._remember_verdict("game.py", "T5", ["Pytest failure: x"])
    first = orch._project_h().vertices["game.py"].history[-1]["version"]
    (orch.workspace_dir / "game.py").write_text('"""Game."""\n\n\ndef size() -> int:\n    """Board size."""\n    return 8\n', encoding="utf-8")
    orch._remember_verdict("game.py", "T5", ["Pytest failure: x"])
    assert first and orch._project_h().vertices["game.py"].history[-1]["version"] != first


def test_a_failure_called_directly_by_the_test_says_the_test_may_be_wrong(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "agent.py").write_text("def act(q, moves):\n    return [q[i] for i in moves]\n", encoding="utf-8")
    (tmp_path / "tests/test_agent.py").write_text("def test_a():\n    act([0.5, 0.0], [0, 2])\n", encoding="utf-8")
    issue = ("Pytest failure:\n_____ test_a _____\ntests/test_agent.py:2: in test_a\n    act([0.5, 0.0], [0, 2])\n"
             "agent.py:2: in act\n    return [q[i] for i in moves]\nE IndexError: index 2 is out of bounds\n")
    [finding] = repair_findings([issue], tmp_path)
    assert finding.file == "agent.py" and "called directly by the test at tests/test_agent.py:2 (`act([0.5, 0.0], [0, 2])`)" in finding.text


def test_a_failing_test_file_is_the_testers_even_when_the_coder_was_its_last_writer(tmp_path: Path) -> None:
    """§XXXI P1, 01 of 2026-11-25: the repair of `tests/test_game.py` went to `seed_coder` three times and was refused three
    times ("test files belong to the tester"); the tester was never asked. The agent follows the file, not `last_writer`."""
    orch = _game_with_test(tmp_path, '    if size() == 9:\n        raise ValueError("the test breaks itself")\n    assert size() > 0\n')
    orch._project_h().vertices["tests/test_game.py"].last_writer = {"agent": "seed_coder", "task_id": "T5"}

    report = orch._run_verification_step(
        {"task_id": "T5", "target_node": "game.py", "assigned_agent": "seed_coder"}, include_docs=False
    )

    assert report["status"] == "FAIL" and report["failed_file"] == "tests/test_game.py"
    assert report["failed_agent"] == "seed_tester"
