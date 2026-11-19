"""§XI (2026-11-18): severity of findings (B0), findings located in the code (B1), repairs aimed at the broken
symbols (B2), a broken example of the plan goes to the plan (B3), the model follows the vertex (B4), and what failed
is frozen and re-planned (A)."""

from __future__ import annotations

import json
from pathlib import Path

from adk.hypergraph.oracles import check_behaviour
from adk.hypergraph.schedule import FAILED, readiness
from adk.mocks import code_fixtures as fx
from adk.mocks.scenarios import config_source
from adk.orchestration.common import _RunState
from adk.orchestration.findings import focus_symbols, repair_findings, symbol_sources
from tests._plans import SPEC, with_plan
from tests.test_root_causes_1115 import _orch

_TASKS = [
    {"task_id": "T1", "target_node": "config.py", "description": "Configuration", "assigned_agent": "seed_coder"},
    {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"},
    {"task_id": "T3", "target_node": "tests/test_core.py", "description": "Tests of core.py", "assigned_agent": "seed_tester"},
]


def _planned(tmp_path: Path):
    orch = _orch(tmp_path)
    h = with_plan(orch, SPEC["interfaces"], SPEC["entrypoint"], _TASKS, [{"index": 1, "title": "Wstęp", "focus": "cel"}])
    return orch, h


def _events(orch, seen: int) -> list[dict]:
    lines = orch.logger.events_path.read_text(encoding="utf-8").splitlines() if orch.logger.events_path.exists() else []
    return [json.loads(line) for line in lines[seen:]]


def _seen(orch) -> int:
    return len(orch.logger.events_path.read_text(encoding="utf-8").splitlines()) if orch.logger.events_path.exists() else 0


# --- B1: doctests of the plan reported per example -------------------------------------------------------------

_MODULE = (
    "def double(x: int) -> int:\n"
    '    """Twice x."""\n'
    "    return x * 3\n"
    "\n\n"
    "def ratio(a: int, b: int) -> float:\n"
    '    """a / b."""\n'
    "    total = a / b\n"
    "    return total\n"
)
_SYMBOLS = {"double": {"kind": "func"}, "ratio": {"kind": "func"}}


def _behaviour(tmp_path: Path, *docstrings: str):
    (tmp_path / "m.py").write_text(_MODULE, encoding="utf-8")
    return check_behaviour(tmp_path, "m.py", {"import": "m", "symbols": _SYMBOLS, "behaviour": list(docstrings)})


def test_a_wrong_result_names_the_symbol_the_example_and_expected_vs_got(tmp_path: Path):
    [v] = _behaviour(tmp_path, "Twice.\n\n>>> double(2)\n4")
    assert v.rule == "BEHAVIOUR_MISMATCH"
    assert "- double: example `double(2)` expected `4`, got `6`" in v.detail
    assert "doctest.py" not in v.detail


def test_an_exception_points_at_the_line_of_the_implementation(tmp_path: Path):
    [v] = _behaviour(tmp_path, "Ratio.\n\n>>> ratio(1, 0)\n0.0")
    assert v.rule == "BEHAVIOUR_MISMATCH"
    assert "raised ZeroDivisionError" in v.detail and "in m.py > ratio, line 8: `total = a / b`" in v.detail


def test_an_example_that_cannot_pass_is_a_defect_of_the_plan(tmp_path: Path):
    """B3: `NameError` in the example's own code, no earlier failure: no implementation can satisfy it."""
    [v] = _behaviour(tmp_path, "Twice.\n\n>>> double(undefined_name)\n2")
    assert v.rule == "SPEC_EXAMPLE_INVALID" and "in the example's own code" in v.detail


def test_a_name_left_undefined_by_an_earlier_failure_is_not_blamed_on_the_plan(tmp_path: Path):
    [v] = _behaviour(tmp_path, "Ratio.\n\n>>> y = ratio(1, 0)\n>>> y\n0.0")
    assert v.rule == "BEHAVIOUR_MISMATCH" and "after an earlier example of the same docstring failed" in v.detail


# --- B1/B2: tool findings located, the symbols to repair --------------------------------------------------------

_CONFIG = 'import os\n\n\nclass Paths:\n    def results(self) -> str:\n        """Dir."""\n        return os.getcwd()\n\n\ndef get_results_dir() -> str:\n    """Dir."""\n    return self.output_path\n'


def test_a_ruff_finding_names_the_function_and_its_line_of_code(tmp_path: Path):
    (tmp_path / "config.py").write_text(_CONFIG, encoding="utf-8")
    [f] = repair_findings(["Ruff lint failure: config.py:12:12: F821 Undefined name `self`\nFound 1 error."], tmp_path)
    assert (f.file, f.symbol, f.line, f.code) == ("config.py", "get_results_dir", 12, "return self.output_path")
    assert str(f) == "config.py > get_results_dir, line 12: `return self.output_path` -- F821 Undefined name `self`"
    assert focus_symbols([f], "config.py") == ["get_results_dir"]


def test_a_pytest_failure_points_at_the_deepest_frame_in_the_workspace(tmp_path: Path):
    (tmp_path / "config.py").write_text(_CONFIG, encoding="utf-8")
    issue = (
        "Pytest failure: F\n___ test_dir ___\ntests/test_config.py:4: in test_dir\n    get_results_dir()\n"
        "config.py:12: in get_results_dir\n    return self.output_path\nE   NameError: name 'self' is not defined\n=== 1 failed ==="
    )
    [f] = repair_findings([issue], tmp_path)
    assert f.symbol == "get_results_dir" and f.text == "test_dir: NameError: name 'self' is not defined"


def test_the_same_finding_is_listed_once_and_symbol_sources_read_methods(tmp_path: Path):
    (tmp_path / "config.py").write_text(_CONFIG, encoding="utf-8")
    issue = "Ruff lint failure: config.py:12:12: F821 Undefined name `self`"
    assert len(repair_findings([issue, issue], tmp_path)) == 1
    sources = symbol_sources(tmp_path, "config.py", ["Paths.results", "get_results_dir"])
    assert sources["Paths.results"].startswith("def results(self)") and "self.output_path" in sources["get_results_dir"]


# --- B0: opinions of the model auditors are warnings ------------------------------------------------------------


def test_model_auditors_cannot_fail_the_defense_their_findings_are_warnings(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    orch.include_docs = False
    (orch.workspace_dir / "config.py").write_text(config_source(fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    opinions = {
        "code_auditor.md": {"status": "FAIL", "issues": ["the code looks fragile"]},
        "redteam_critic_guard.md": {"status": "FAIL", "gate_3_approved": False, "issues": ["the thesis overclaims"]},
    }
    orch._call_agent = lambda md, *_a, **_k: {"status": "ok", "output": dict(opinions.get(Path(md).name, {"status": "PASS", "issues": []}))}
    report = orch._run_verification_step({"task_id": "FINAL", "target_node": "core.py"}, include_docs=False, is_final_gate=True)
    assert report["status"] == "PASS"
    assert {"the code looks fragile", "the thesis overclaims"} <= set(report["warnings"])


# --- B2/B4: the fast repair names the broken symbols; the model follows the vertex -------------------------------


def _repair_once(tmp_path: Path, failures: int) -> tuple[dict, str]:
    from adk.orchestration import repair

    orch, h = _planned(tmp_path)
    core = fx.TICTACTOE_CORE_CODE
    (orch.workspace_dir / "core.py").write_text(core, encoding="utf-8")
    line = next(i for i, text in enumerate(core.splitlines(), 1) if text.startswith("def check_winner("))
    h.vertices["core.py"].failures = failures
    built: list[tuple[dict, str]] = []
    orch._execute_builder_step = lambda task, model_tier="SML", **_k: built.append((task, model_tier))
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda *_a, **_k: False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder",
               "issues": [f"Ruff lint failure: core.py:{line + 2}:5: F821 Undefined name `x`"], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"}
    state = _RunState(user_prompt="p", max_retries=repair.FAST_REPAIR_ATTEMPTS, multi_cycle_waves=True, tasks=[task])
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    return built[0]


def test_a_fast_repair_names_the_broken_symbol_and_carries_its_code(tmp_path: Path):
    task, tier = _repair_once(tmp_path, failures=0)
    assert task["description"].startswith("Fix `check_winner` in core.py")
    assert task["task_context"] == "Implement core.py"
    assert task["repair_focus"]["file"] == "core.py" and task["repair_focus"]["symbols"]["check_winner"].startswith("def check_winner(")
    assert tier == "SML"


def test_the_large_model_takes_over_a_vertex_after_its_second_failure(tmp_path: Path):
    _task, tier = _repair_once(tmp_path, failures=2)
    assert tier == "LRM"


def test_failures_are_counted_on_the_vertex_across_tasks(tmp_path: Path):
    orch, h = _planned(tmp_path)
    orch._remember_verdict("core.py", "T2", ["BEHAVIOUR_MISMATCH [core.py]: x"])
    orch._remember_verdict("core.py", "Q1_FIX_core_2", ["ANSWER_REJECTED: y"])
    assert h.vertices["core.py"].failures == 2 and orch._vertex_failures("core.py") == 2


# --- B3: a broken example goes to the plan at once --------------------------------------------------------------


def test_a_broken_example_asks_the_planner_at_its_first_occurrence(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    asked: list[str] = []
    orch._call_agent = lambda md, *_a, **_k: asked.append(Path(md).name) or {"status": "ok", "output": {"decision": "KEEP", "reason": "fine"}}
    assert orch._amend_spec_if_wrong("core.py", ["BEHAVIOUR_MISMATCH [core.py]: wrong value"], "T2") is False
    assert asked == []  # an ordinary mismatch waits for a repetition
    orch._amend_spec_if_wrong("core.py", ["SPEC_EXAMPLE_INVALID [core.py]: the example itself raises NameError"], "T2")
    assert asked == ["plan_change_guard.md"]


# --- A: what failed is frozen, its dependents wait, the failed part is re-planned --------------------------------


def test_a_test_waits_for_its_module_to_be_verified(tmp_path: Path):
    _orch_, h = _planned(tmp_path)
    h.vertices["core.py"].state = "impl"
    assert readiness(h, "tests/test_core.py", set()) == ["core.py is not verified yet"]
    h.vertices["core.py"].state = "verified"
    assert readiness(h, "tests/test_core.py", set()) == []


def test_a_module_never_builds_on_a_failed_one(tmp_path: Path):
    _orch_, h = _planned(tmp_path)
    assert "config.py" in h.edges["I:core.py"].spec.get("uses", {})
    h.vertices["config.py"].state = FAILED
    assert readiness(h, "core.py", set()) == ["config.py failed; it waits for its re-plan"]


def test_a_task_failing_for_another_vertex_is_deferred_to_it(tmp_path: Path):
    orch, h = _planned(tmp_path)
    test_task = _TASKS[2]
    blamed = orch._mark_failed({"failed_file": "core.py"}, test_task)
    assert blamed == "core.py" and h.vertices["core.py"].state == FAILED
    assert orch._waits_on_failed(test_task)


def test_the_failed_part_is_re_planned_from_its_dossier(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = FAILED
    h.vertices["config.py"].history.append({"task_id": "T1", "issues": ["ANSWER_REJECTED: SyntaxError"]})
    h.vertices["thesis.md#ch1"].state = "verified"
    sent: list[dict] = []
    answer = {"tasks": [
        {"target_node": "config.py", "description": "Write the constants only", "assigned_agent": "seed_coder"},
        {"target_node": "thesis.md", "description": "Chapter 1: rewrite", "assigned_agent": "seed_writer"},
        {"target_node": "nowhere.py", "description": "?"},
    ]}
    orch._call_agent = lambda _md, payload, **_k: sent.append(payload) or {"status": "ok", "output": answer}
    seen = _seen(orch)
    state = _RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=[])
    result = orch._replan_failed(state)
    assert [(t["task_id"], t["target_node"]) for t in result["tasks"]] == [("R1_1", "config.py")]
    assert state.tasks == result["tasks"]
    dossier = sent[0]["repair_dossier"]
    assert [e["vertex"] for e in dossier["failed"]] == ["config.py"]
    assert dossier["failed"][0]["history"][-1]["issues"] == ["ANSWER_REJECTED: SyntaxError"]
    assert "thesis.md#ch1" in dossier["verified_do_not_touch"] and "core.py" in dossier["failed"][0]["waiting_on_it"]
    replanned = [e for e in _events(orch, seen) if e["event"] == "REPLANNED"]
    assert replanned and replanned[0]["tasks"] == ["R1_1"] and len(replanned[0]["dropped"]) == 2


def test_re_planning_without_progress_ends_the_run_with_gaps(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = FAILED
    orch._call_agent = lambda *_a, **_k: {"status": "ok", "output": {"tasks": []}}
    orch._audit_factual_state = lambda _report: {}
    orch._finalize_with_gaps = lambda _audit, _report: {"gaps": [{"kind": "kod", "detail": "config.py"}], "pdf_ok": False}
    orch._shout_problem_stop = lambda _msg: None
    state = _RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=[])
    assert "tasks" in orch._replan_failed(state) and "tasks" in orch._replan_failed(state)
    stop = orch._replan_failed(state)["stop"]
    assert stop["status"] == "COMPLETED_WITH_GAPS" and stop["reason"] == "REPLAN_EXHAUSTED" and stop["failed_vertices"] == ["config.py"]


def test_nothing_failed_means_no_re_plan(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    orch._call_agent = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no planner call expected"))
    assert orch._replan_failed(_RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=[])) is None
