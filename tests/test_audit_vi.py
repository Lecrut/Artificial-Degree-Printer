"""Regression tests for Audit VI (audit_repairs.md §VII), reproduced from the 01/02 runs of 2026-11-16."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from adk.core.logger import set_process_log_dir
from main import run_scenario


def _clone_adk_env(tmp_path: Path) -> Path:
    src_adk = Path(__file__).resolve().parent.parent / "adk"
    dst_adk = tmp_path / "adk"
    for part in ("state", "agents", "tools"):
        shutil.copytree(src_adk / part, dst_adk / part)
    (dst_adk / "workspace").mkdir(parents=True, exist_ok=True)
    return dst_adk


def _events(log_dir: Path) -> list[dict]:
    path = log_dir / "events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_a1_run_writes_task_outcomes_and_verdicts_to_events(tmp_path: Path):
    """T3: the process log had 86 verification starts and not one verdict; outcomes must be machine-readable."""
    log_dir = tmp_path / "logs"
    set_process_log_dir(log_dir)
    try:
        result = run_scenario("1", provider="mock", adk_root=_clone_adk_env(tmp_path))
    finally:
        set_process_log_dir(None)
    assert result["status"] == "COMPLETED"
    kinds = [e["event"] for e in _events(log_dir)]
    assert "TASK_START" in kinds and "VERDICT" in kinds and "TASK_DONE" in kinds
    verdict = next(e for e in _events(log_dir) if e["event"] == "VERDICT")
    assert verdict["status"] in ("PASS", "FAIL") and verdict["task_id"]


# --- A2: ast_editor never appends, overwrites or edits dead code silently (Audit VI X3) ---------------------

from adk.tools.building.ast_editor import declared_names, edit_ast_node, whole_module_loss  # noqa: E402

_EXPERIMENT = (
    '"""Experiment entrypoint."""\n'
    "from src.config import CHANNELS, NOISE_LEVELS, N_REPETITIONS\n"
    "from src.data_types import SignalSample\n\n\n"
    "def run_experiment():\n"
    "    return [CHANNELS, NOISE_LEVELS, N_REPETITIONS]\n"
)


def test_a2_unknown_public_symbol_is_refused_with_existing_names(tmp_path: Path):
    """02, 16:53:35: edits of `fit`/`predict` aimed at experiment.py became module functions."""
    path = tmp_path / "src" / "experiment.py"
    path.parent.mkdir()
    path.write_text(_EXPERIMENT, encoding="utf-8")
    planned = declared_names(_EXPERIMENT)  # the plan's interface of experiment.py: only run_experiment
    res = edit_ast_node(path, "fit", "def fit(self, samples):\n    pass\n", planned=planned)
    assert res["status"] == "error" and res["guard"] == "TARGET_NOT_FOUND"
    assert "run_experiment" in res["error"]
    assert path.read_text(encoding="utf-8") == _EXPERIMENT
    # a symbol the plan declares may be added
    assert edit_ast_node(path, "fit", "def fit():\n    pass\n", planned=planned | {"fit"})["action"] == "appended"


def test_a2_snippet_without_target_or_with_extra_definitions_is_refused(tmp_path: Path):
    """02, 17:25:00: symbol `__main__` with three defs appended the last one (`predict`)."""
    path = tmp_path / "experiment.py"
    path.write_text(_EXPERIMENT, encoding="utf-8")
    no_target = edit_ast_node(path, "__main__", "def fit(self):\n    pass\n\ndef predict(self):\n    pass\n")
    assert no_target["guard"] == "TARGET_NOT_IN_CODE"
    extra = edit_ast_node(path, "run_experiment", "def run_experiment():\n    return 1\n\ndef fit(self):\n    pass\n")
    assert extra["guard"] == "EXTRA_DEFINITIONS" and "fit" in extra["error"]
    assert path.read_text(encoding="utf-8") == _EXPERIMENT


def test_a2_duplicate_definition_is_refused(tmp_path: Path):
    """02: three `run_experiment` in experiment.py, edits replaced the first while Python ran the last."""
    path = tmp_path / "experiment.py"
    path.write_text(_EXPERIMENT + "\n\ndef run_experiment():\n    return None\n", encoding="utf-8")
    res = edit_ast_node(path, "run_experiment", "def run_experiment():\n    return 2\n")
    assert res["guard"] == "DUPLICATE_DEFINITION"


def test_a2_import_of_an_already_imported_module_drops_stale_names(tmp_path: Path):
    """02: the stale `from src.config import N_REPETITIONS` could never be removed and was the final ImportError."""
    path = tmp_path / "experiment.py"
    path.write_text(_EXPERIMENT, encoding="utf-8")
    res = edit_ast_node(
        path,
        "run_experiment",
        "from src.config import get_channels\n\ndef run_experiment():\n    return [get_channels(), SignalSample]\n",
    )
    assert res["status"] == "ok"
    source = path.read_text(encoding="utf-8")
    assert source.count("from src.config import") == 1
    assert "get_channels" in source and "N_REPETITIONS" not in source and "CHANNELS," not in source
    assert "from src.data_types import SignalSample" in source  # other modules' imports untouched


def test_a2_used_old_names_survive_the_import_merge(tmp_path: Path):
    path = tmp_path / "mod.py"
    path.write_text("from typing import List\n\n\ndef a() -> List[int]:\n    return []\n\n\ndef b():\n    return 1\n", encoding="utf-8")
    assert edit_ast_node(path, "b", "from typing import Any\n\ndef b() -> Any:\n    return 1\n")["status"] == "ok"
    source = path.read_text(encoding="utf-8")
    assert "List" in source and "Any" in source and source.count("from typing import") == 1


def test_a2_tests_and_private_helpers_may_still_be_added(tmp_path: Path):
    test_file = tmp_path / "tests" / "test_mod.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_a():\n    assert True\n", encoding="utf-8")
    assert edit_ast_node(test_file, "test_b", "def test_b():\n    assert True\n")["status"] == "ok"
    module = tmp_path / "mod.py"
    module.write_text("def a():\n    return 1\n", encoding="utf-8")
    planned = {"a"}
    assert edit_ast_node(module, "_helper", "def _helper():\n    return 2\n", planned=planned)["action"] == "appended"
    assert edit_ast_node(module, "__main__", "if __name__ == '__main__':\n    a()\n", planned=planned)["action"] == "appended"


def test_a2_whole_module_answer_may_not_drop_public_symbols():
    """02, 17:24:51: symbol `src.experiment` with three import lines overwrote the whole file."""
    assert whole_module_loss(_EXPERIMENT, "import numpy as np\nimport pandas as pd\n") == ["run_experiment"]
    assert whole_module_loss(_EXPERIMENT, _EXPERIMENT.replace("return [", "return (")) == []


# --- A3: the hypergraph as specification (Audit VI §VII.12) -------------------------------------------------------

from adk.hypergraph import build_from_plan, code_violations, diff, load, observe  # noqa: E402

_CONFIG = '"""Config."""\nCHANNELS: list[str] = ["EEG", "ECG"]\nN_REPETITIONS: int = 3\nSEEDS: list[int] = [0, 1, 2]\n'
_GENERATOR = (
    '"""Generator."""\nfrom src.config import CHANNELS\n\n\n'
    "def generate_sample(channel: str, seed: int) -> list[float]:\n"
    '    """One sample."""\n    pass\n'
)
_EXPERIMENT_IFACE = (
    '"""Entrypoint."""\nfrom src.config import CHANNELS, N_REPETITIONS, SEEDS\n'
    "from src.data_generator import generate_sample\n\n\n"
    "def run_experiment() -> list[dict]:\n"
    '    """Run everything."""\n    pass\n'
)
_GOOD = {"src/config.py": _CONFIG, "src/data_generator.py": _GENERATOR, "src/experiment.py": _EXPERIMENT_IFACE}
_ENTRY = "src/experiment.py:run_experiment"


def _rules(violations) -> set[str]:
    return {v.rule for v in violations}


def test_a3_a_valid_plan_has_no_violations():
    specs, violations = code_violations(_GOOD, _ENTRY)
    assert violations == []
    assert specs["src/config.py"]["symbols"]["SEEDS"] == {"kind": "const", "type": "list[int]"}
    assert specs["src/experiment.py"]["uses"] == {"src/config.py": ["CHANNELS", "N_REPETITIONS", "SEEDS"], "src/data_generator.py": ["generate_sample"]}


def test_a3_the_plans_of_01_and_02_are_rejected_before_any_code():
    """X2: 02 had `SEEDS = field(...)` and `List` without import; 01 had `run_experiments(config)`."""
    broken_config = _CONFIG.replace("SEEDS: list[int] = [0, 1, 2]", "from dataclasses import field\nSEEDS: list[int] = field(default_factory=list)")
    broken_generator = _GENERATOR.replace("-> list[float]", "-> List[float]")
    broken_entry = _EXPERIMENT_IFACE.replace("def run_experiment()", "def run_experiment(config: dict)")
    _, violations = code_violations(
        {"src/config.py": broken_config, "src/data_generator.py": broken_generator, "src/experiment.py": broken_entry}, _ENTRY
    )
    by_rule = {v.rule: v for v in violations}
    assert by_rule["CONSTANT_TYPE_MISMATCH"].vertex == "src/config.py" and "Field" in by_rule["CONSTANT_TYPE_MISMATCH"].detail
    assert any(v.rule == "STUB_DOES_NOT_IMPORT" and "List" in v.detail and v.culprit == "src/data_generator.py" for v in violations)
    assert "ENTRYPOINT_HAS_ARGUMENTS" in by_rule


def test_a3_undeclared_uses_duplicate_modules_and_missing_packages_are_violations():
    uses_missing = {**_GOOD, "src/experiment.py": _EXPERIMENT_IFACE.replace("SEEDS", "SEED_VALUE")}
    assert "USES_UNDECLARED" in _rules(code_violations(uses_missing, _ENTRY)[1])
    duplicate = {**_GOOD, "config.py": _CONFIG}
    assert "DUPLICATE_MODULE" in _rules(code_violations(duplicate, _ENTRY)[1])
    no_package = {**_GOOD, "src/data_generator.py": "import surely_not_installed_pkg\n" + _GENERATOR}
    assert "PACKAGE_UNAVAILABLE" in _rules(code_violations(no_package, _ENTRY)[1])


def _h():
    tasks = [
        {"task_id": "T1", "target_node": "tests/test_data_generator.py", "description": "tests", "assigned_agent": "seed_tester"},
        {"task_id": "T2", "target_node": "docs/literature_review.md", "description": "survey", "assigned_agent": "background_researcher"},
    ]
    chapters = [{"index": 1, "title": "Wstęp", "focus": "cel"}, {"index": 4, "title": "Wyniki", "focus": "eksperyment"}]
    return build_from_plan(_GOOD, _ENTRY, tasks, chapters, ["f1"])


def test_a3_build_gives_typed_bags_roles_and_order():
    h, problems = _h()
    assert problems == []
    assert h.edges["I:src/config.py"].members == {"src/config.py": "P", "src/data_generator.py": "C", "src/experiment.py": "C"}
    assert h.edges["I:src/data_generator.py"].members["tests/test_data_generator.py"] == "T"
    assert h.edges["R:run"].members == {"src/experiment.py": "P", "results.csv": "O"}
    assert ("R:run", "N:thesis.md#ch4") in h.order and ("R:run", "N:thesis.md#ch1") not in h.order
    assert h.vertices["src/experiment.py"].kind == "entry" and h.vertices["src/config.py"].state == "stub"
    # blast radius = own bags + everything after them in ≺: a config change reaches the results chapter
    assert {"I:src/config.py", "I:src/experiment.py", "R:run", "N:thesis.md#ch4"} <= h.blast_radius("src/config.py")
    assert "N:thesis.md#ch1" not in h.blast_radius("src/config.py")


def test_a3_diff_finds_appended_symbols_stale_imports_and_files_outside_the_plan(tmp_path: Path):
    """X3/X4 as seen by H_obs − H: `fit` appended to experiment.py, getters instead of constants, `_iforest.py`."""
    h, _ = _h()
    ws = tmp_path / "ws"
    for rel, source in _GOOD.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(source, encoding="utf-8")
    assert diff(h, observe(ws, h)) == []
    (ws / "src/experiment.py").write_text(_EXPERIMENT_IFACE + "\n\ndef fit(self, samples):\n    pass\n", encoding="utf-8")
    (ws / "src/config.py").write_text('def get_channels() -> list[str]:\n    return ["EEG"]\n', encoding="utf-8")
    (ws / "_iforest.py").write_text("X = 1\n", encoding="utf-8")
    found = {(v.rule, v.culprit) for v in diff(h, observe(ws, h))}
    assert ("API_EXTRA", "src/experiment.py") in found
    assert ("API_MISSING", "src/config.py") in found and ("API_EXTRA", "src/config.py") in found
    assert ("FILE_OUTSIDE_PLAN", "_iforest.py") in found


def test_a3_planning_returns_violations_to_the_planner_then_builds_h_and_stubs(tmp_path: Path):
    from tests.test_root_causes_1115 import _orch

    orch = _orch(tmp_path)
    broken = {"tasks": [{"task_id": "T1", "target_node": "src/experiment.py", "description": "x"}],
              "interfaces": {**_GOOD, "src/experiment.py": _EXPERIMENT_IFACE.replace("run_experiment()", "run_experiment(config)")},
              "entrypoint": _ENTRY}
    fixed = {**broken, "interfaces": _GOOD}
    sent: list[dict] = []

    def planner(_md, payload, **_kw):
        sent.append(payload)
        return {"status": "ok", "output": fixed}

    orch._call_agent = planner
    plan, interfaces, violations = orch._validated_plan(broken, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert violations == [] and plan is fixed and len(sent) == 1
    assert "ENTRYPOINT_HAS_ARGUMENTS" in sent[0]["error_feedback"]

    h = orch._build_project_hypergraph(interfaces, {"entrypoint": _ENTRY, "metrics": ["f1"]}, fixed["tasks"])
    assert h is not None and load(orch.hypergraph_path).edges.keys() == h.edges.keys()
    stub = (orch.workspace_dir / "src/experiment.py").read_text(encoding="utf-8")
    assert "raise NotImplementedError" in stub


def test_a3_a_plan_still_broken_after_two_corrections_stops_the_run(tmp_path: Path):
    from tests.test_root_causes_1115 import _orch

    orch = _orch(tmp_path)
    broken = {"tasks": [{"task_id": "T1", "target_node": "src/experiment.py", "description": "x"}],
              "interfaces": {**_GOOD, "src/data_generator.py": _GENERATOR.replace("-> list[float]", "-> List[float]")},
              "entrypoint": _ENTRY}
    calls = []
    orch._call_agent = lambda *_a, **_k: calls.append(1) or {"status": "ok", "output": broken}
    _, _, violations = orch._validated_plan(broken, {}, tmp_path / "planner.md")
    assert len(calls) == 2 and any("STUB_DOES_NOT_IMPORT" in v for v in violations)
    assert orch._plan_rejected(violations, broken["tasks"])["stop"]["status"] == "PLAN_REJECTED"


# --- A5: writes and verification judged against σ; pointer findings go to the writer -----------------------------

import pytest  # noqa: E402

from adk.orchestration.common import MaterializationError  # noqa: E402


def _spec_orch(tmp_path: Path):
    from tests.test_root_causes_1115 import _orch

    orch = _orch(tmp_path)
    orch.include_docs = False
    orch._build_project_hypergraph(_GOOD, {"entrypoint": _ENTRY}, [])
    return orch


def test_a5_rewriting_the_planned_config_into_getters_is_rejected(tmp_path: Path):
    """X4, 02: T3 rewrote config constants into get_channels() and the getters became the contract."""
    orch = _spec_orch(tmp_path)
    before = (orch.workspace_dir / "src/config.py").read_text(encoding="utf-8")
    getters = {"files": [{"filename": "src/config.py", "content": 'def get_channels() -> list[str]:\n    return ["EEG"]\n'}]}
    with pytest.raises(MaterializationError) as exc:
        orch._materialize_workspace_artifact("src/config.py", getters)
    assert "API_MISSING" in str(exc.value) and "CHANNELS" in str(exc.value)
    assert (orch.workspace_dir / "src/config.py").read_text(encoding="utf-8") == before


def test_a5_contract_change_cannot_remove_what_other_modules_use(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    answer = {
        "files": [{"filename": "src/config.py", "content": 'def get_channels() -> list[str]:\n    return ["EEG"]\n'}],
        "contract_change": {"reason": "getters are nicer"},
    }
    with pytest.raises(MaterializationError) as exc:
        orch._materialize_workspace_artifact("src/config.py", answer)
    assert "src/data_generator.py is planned to use them" in str(exc.value)


def test_a5_contract_change_may_add_to_the_interface(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    added = _CONFIG + "TEST_SPLIT: float = 0.2\n"
    orch._materialize_workspace_artifact(
        "src/config.py", {"files": [{"filename": "src/config.py", "content": added}], "contract_change": {"reason": "split ratio"}}
    )
    assert "TEST_SPLIT" in load(orch.hypergraph_path).edges["I:src/config.py"].spec["symbols"]
    assert any('"SPEC_CHANGED"' in line for line in (orch.logger.events_path.read_text(encoding="utf-8").splitlines()))


def test_a5_files_outside_the_plan_and_appended_public_symbols_are_rejected(tmp_path: Path):
    """X3/X4, 02: `_iforest.py` in the root and `validation.py` became nodes and contract."""
    orch = _spec_orch(tmp_path)
    with pytest.raises(MaterializationError) as exc:
        orch._materialize_workspace_artifact("_iforest.py", {"files": [{"filename": "_iforest.py", "content": "X = 1\n"}]})
    assert "FILE_OUTSIDE_PLAN" in str(exc.value)
    assert not (orch.workspace_dir / "_iforest.py").exists()


def test_a5_verification_blames_the_side_that_breaks_the_specification(tmp_path: Path):
    """X5: the importer was blamed, the definition side never; σ decides."""
    orch = _spec_orch(tmp_path)
    (orch.workspace_dir / "src/experiment.py").write_text(_EXPERIMENT_IFACE.replace("SEEDS", "SEED_VALUE"), encoding="utf-8")
    report = orch._run_verification_step({"task_id": "T9", "target_node": "src/experiment.py"})
    assert report["status"] == "FAIL" and report["failed_file"] == "src/experiment.py"
    assert any("IMPORT_OUTSIDE_SPEC" in str(i) for i in report.get("issues", []) + report.get("errors", []) + [report])


def test_a5_pointer_findings_are_the_writers_whatever_file_they_name():
    """X6, 02: "Symbol 'CONFIG' not found in 'config.py'" became a coder task on src/config.py."""
    from adk.orchestration.recovery import _is_pointer_finding

    assert _is_pointer_finding("Symbol 'CONFIG' not found in 'config.py' Closest existing targets: src/config.py:CHANNELS.")
    assert _is_pointer_finding("File 'src' does not exist (it is a directory, not a file) A path inside a pointer is separated by a slash")
    assert not _is_pointer_finding("Import error in experiment.py: ImportError: cannot import name 'N_REPETITIONS'")


# --- A4: behaviour in σ, tests only through σ, tests validated on the stubs --------------------------------------

from adk.hypergraph.oracles import check_behaviour, validate_test_on_stubs  # noqa: E402

_BASELINE = (
    '"""Z-score baseline."""\n\n\nclass ZScoreBaseline:\n'
    '    """Detector."""\n    threshold: float\n\n'
    "    def __init__(self, threshold: float = 3.0) -> None:\n"
    '        """Create."""\n        self.threshold = threshold\n\n'
    "    def score(self, x: float) -> float:\n"
    '        """Absolute score.\n\n        >>> ZScoreBaseline().score(-2.0)\n        2.0\n        """\n'
    "        return abs(x)\n"
)
_SPEC_IFACES = {"src/baseline.py": _BASELINE, "src/experiment.py": '"""E."""\n\n\ndef run_experiment() -> int:\n    """Run."""\n    return 0\n'}


def _baseline_h(tmp_path: Path):
    h, problems = build_from_plan(
        _SPEC_IFACES, "src/experiment.py:run_experiment",
        [{"task_id": "T1", "target_node": "tests/test_baseline.py", "description": "t", "assigned_agent": "seed_tester"}], [], [],
    )
    assert problems == []
    ws = tmp_path / "ws"
    for rel, source in _SPEC_IFACES.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(source, encoding="utf-8")
    (ws / "tests").mkdir()
    return h, ws


def test_a4_tests_may_read_only_declared_attributes(tmp_path: Path):
    """T1, 02 T10: `hasattr(model, 'mean_')` — an attribute the interface declared nowhere."""
    h, ws = _baseline_h(tmp_path)
    assert h.edges["I:src/baseline.py"].spec["symbols"]["ZScoreBaseline.threshold"] == {"kind": "attr"}
    (ws / "tests/test_baseline.py").write_text(
        "from src.baseline import ZScoreBaseline\n\n\ndef test_fit():\n    m = ZScoreBaseline(3.0)\n"
        "    assert m.threshold == 3.0\n    assert hasattr(m, 'mean_')\n",
        encoding="utf-8",
    )
    found = [v for v in diff(h, observe(ws, h)) if v.rule == "TEST_OUTSIDE_SPEC"]
    assert len(found) == 1 and "ZScoreBaseline.mean_" in found[0].detail and "threshold" not in found[0].detail


def test_a4_a_test_is_validated_on_the_stubs_before_any_implementation(tmp_path: Path):
    """T1, 02 T11: `np` without import; T9: a wrong import path — both found on the stubs."""
    h, ws = _baseline_h(tmp_path)
    good = ws / "tests/test_baseline.py"
    good.write_text("from src.baseline import ZScoreBaseline\n\n\ndef test_score():\n    assert ZScoreBaseline().score(-2.0) == 2.0\n", encoding="utf-8")
    assert validate_test_on_stubs(ws, "tests/test_baseline.py", h) == []
    good.write_text(
        "from src.baseline import ZScoreBaseline\n\n\ndef test_score():\n    x = np.array([1.0])\n    assert ZScoreBaseline().score(x[0]) == 1.0\n",
        encoding="utf-8",
    )
    bad = validate_test_on_stubs(ws, "tests/test_baseline.py", h)
    assert bad and bad[0].rule == "TEST_INVALID_ON_STUBS" and "NameError" in bad[0].detail
    good.write_text("from baseline import ZScoreBaseline\n\n\ndef test_score():\n    assert ZScoreBaseline().score(1.0) == 1.0\n", encoding="utf-8")
    assert validate_test_on_stubs(ws, "tests/test_baseline.py", h)[0].rule == "TEST_INVALID_ON_STUBS"


def test_a4_behaviour_examples_of_the_plan_judge_the_implementation(tmp_path: Path):
    h, ws = _baseline_h(tmp_path)
    spec = h.edges["I:src/baseline.py"].spec
    assert check_behaviour(ws, "src/baseline.py", spec) == []
    (ws / "src/baseline.py").write_text(_BASELINE.replace("return abs(x)", "return x"), encoding="utf-8")
    broken = check_behaviour(ws, "src/baseline.py", spec)
    assert broken and broken[0].rule == "BEHAVIOUR_MISMATCH" and broken[0].culprit == "src/baseline.py"
    (ws / "src/baseline.py").write_text(_BASELINE.replace("        return abs(x)", "        raise NotImplementedError"), encoding="utf-8")
    assert check_behaviour(ws, "src/baseline.py", spec) == []  # a stub is not judged on behaviour yet


# --- A6: results come from the current code (Φ_R freshness) -------------------------------------------------------


def test_a6_a_code_change_after_the_experiment_makes_the_results_stale_and_reruns_them(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    runs: list[str] = []
    orch._refresh_experiment_after_code = lambda node: runs.append(node)
    orch._record_data_produced()
    assert load(orch.hypergraph_path).edges["R:run"].fingerprint
    orch._ensure_fresh_results()
    assert runs == []  # nothing changed since the results were produced
    (orch.workspace_dir / "src/config.py").write_text(_CONFIG.replace("3", "5"), encoding="utf-8")
    orch._ensure_fresh_results()
    assert runs == ["src/experiment.py"]
    assert any('"DATA_STALE"' in line for line in orch.logger.events_path.read_text(encoding="utf-8").splitlines())


# --- A7: work from the state of H — readiness instead of a queue that blocks by file and loses work --------------

from adk.hypergraph.schedule import readiness, vertex_of  # noqa: E402
from adk.orchestration.common import _RunState  # noqa: E402


def _run_order(orch, tasks, fail: set[str] = frozenset()) -> list[str]:
    state = _RunState(user_prompt="p", max_retries=1, multi_cycle_waves=True, tasks=tasks)
    order = []
    for _idx, task in orch._task_order(state):
        order.append(task["task_id"])
        task["status"] = "FAILED" if task["task_id"] in fail else "DONE"
        if task["task_id"] not in fail:
            vertex = orch._task_vertex(task)
            orch._set_vertex_state(vertex, "impl")
    return order


def _tasks(*pairs):
    return [{"task_id": tid, "target_node": target, "description": f"implement {target}", "status": "TODO"} for tid, target in pairs]


def test_a7_a_module_runs_after_the_modules_it_uses_whatever_the_plan_order(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    tasks = _tasks(("T1", "src/experiment.py"), ("T2", "src/config.py"), ("T3", "src/data_generator.py"))
    assert _run_order(orch, tasks) == ["T2", "T3", "T1"]


def test_a7_a_failure_blocks_only_what_depends_on_it_and_nothing_is_lost(tmp_path: Path):
    """X1: the failed SKELETON blocked every later task on the entrypoint file, and rebuilt queues dropped them."""
    orch = _spec_orch(tmp_path)
    tasks = _tasks(("T1", "src/config.py"), ("T2", "src/data_generator.py"), ("T3", "src/config.py"))
    # the second task on the same file still runs (no block by file); once config has code, its user may run
    assert _run_order(orch, tasks, fail={"T1"}) == ["T1", "T3", "T2"]

    orch = _spec_orch(tmp_path / "again")
    tasks = _tasks(("T1", "src/config.py"), ("T2", "src/data_generator.py"), ("T3", "src/config.py"))
    assert _run_order(orch, tasks, fail={"T1", "T3"}) == ["T1", "T3"]
    assert tasks[1]["status"] == "WAITING"  # the generator waits for config, it is not dropped
    carried = orch._carry_over(tasks)
    assert [t["task_id"] for t in carried] == ["T2"] and carried[0]["status"] == "TODO"


def test_a7_a_results_chapter_waits_for_current_results():
    """01: the conclusions claimed the thesis was not confirmed while no results existed."""
    h, _ = _h()
    assert vertex_of(h, "thesis.md", "[Increment 3] Write Chapter 4 (Results) of thesis.md") == "thesis.md#ch4"
    assert readiness(h, "thesis.md#ch4", set()) == ["results.csv: the experiment has not produced current results"]
    assert readiness(h, "thesis.md#ch1", set()) == []
    h.vertices["results.csv"].state = "verified"
    assert readiness(h, "thesis.md#ch4", set()) == []


def test_a8_a_code_task_sees_its_specification_and_history_not_the_writers_grounding(tmp_path: Path):
    """X5 (no memory of earlier attempts) and U7 (writer directives in the coder's payload, `\ref_csv` in code)."""
    orch = _spec_orch(tmp_path)
    orch._remember_verdict("src/data_generator.py", "T6", ["IMPORT_OUTSIDE_SPEC: imports SEED_VALUE"])
    payload = {
        "exports": {"src/config.py": {}, "src/data_generator.py": {}, "src/experiment.py": {}},
        "grounded_hypergraph_state": {"mandatory_directives": ["Draw TikZ"]},
        "hypergraph_nodes": {}, "active_edges": {},
    }
    orch._spec_payload(payload, {"task_id": "T6_FIX1", "target_node": "src/data_generator.py", "description": "x"})
    assert sorted(payload["specification"]) == ["src/config.py", "src/data_generator.py"]
    assert payload["specification"]["src/config.py"]["symbols"]["CHANNELS"]["kind"] == "const"
    assert sorted(payload["exports"]) == ["src/config.py", "src/data_generator.py"]
    assert payload["previous_attempts"][0]["task_id"] == "T6"
    assert "grounded_hypergraph_state" not in payload and "hypergraph_nodes" not in payload


# --- A9/A10: a known culprit goes back to its author, not to the planner; σ breaches make no prompt rules -------

from adk.orchestration.common import HARNESS_ENFORCED_CATEGORIES, _issue_category  # noqa: E402


def test_a10_breaches_of_the_specification_are_enforced_by_the_harness_not_by_rules():
    category = _issue_category(["IMPORT_OUTSIDE_SPEC [src/experiment.py]: imports N_REPETITIONS from src/config.py"])
    assert category == "spec" and category in HARNESS_ENFORCED_CATEGORIES
    assert _issue_category(["BEHAVIOUR_MISMATCH [src/baseline.py]: the implementation does not give the results"]) != "spec"


def test_a9_with_a_known_culprit_the_remediation_planner_is_skipped(tmp_path: Path):
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
    assert calls == ["T2_FIX1", "T2_FIX2"]  # two local attempts by the author, no planner


# --- End to end: the spec-driven path with a scripted model ----------------------------------------------------

_E2E_GAME = (
    "from src.config import N_GAMES\n\n\ndef play(seed: int) -> int:\n"
    '    """Wins in N_GAMES games.\n\n    >>> play(0) >= 0\n    True\n    """\n    ...\n'
)
_E2E_EXPERIMENT = 'from src.config import SEEDS\nfrom src.game import play\n\n\ndef run_experiment() -> list[int]:\n    """Wins per seed."""\n    ...\n'
_E2E_IFACES = {"src/config.py": "N_GAMES: int = 3\nSEEDS: list[int] = [0, 1]\n", "src/game.py": _E2E_GAME, "src/experiment.py": _E2E_EXPERIMENT}
_E2E_IMPL = {
    "src/config.py": _E2E_IFACES["src/config.py"],
    "src/game.py": 'from src.config import N_GAMES\n\n\ndef play(seed: int) -> int:\n    """Wins."""\n    return (seed + N_GAMES) % 2\n',
    "src/experiment.py": 'from src.config import SEEDS\nfrom src.game import play\n\n\ndef run_experiment() -> list[int]:\n    """Wins."""\n    return [play(s) for s in SEEDS]\n',
}


def _e2e(tmp_path: Path, implement_entry: bool = True) -> tuple[dict, list[str], list[dict]]:
    from adk.core.llm import set_llm_handler
    from adk.orchestrator import NeuroSymbolicOrchestrator

    built: list[str] = []

    def handler(system_prompt, payload, _tier):
        if "Task Planner" in system_prompt:
            return {
                "tasks": [
                    {"task_id": "T1", "target_node": "src/experiment.py", "description": "Implement run_experiment", "assigned_agent": "seed_coder"},
                    {"task_id": "T2", "target_node": "src/config.py", "description": "Implement config", "assigned_agent": "seed_coder"},
                    {"task_id": "T3", "target_node": "src/game.py", "description": "Implement play", "assigned_agent": "seed_coder"},
                    {"task_id": "T4", "target_node": "tests/test_game.py", "description": "Test play", "assigned_agent": "seed_tester"},
                ],
                "interfaces": _E2E_IFACES,
                "entrypoint": "src/experiment.py:run_experiment",
            }
        if "Critic Guard" in system_prompt:
            return {"status": "PASS", "approved": True, "issues": []}
        target = str(payload.get("target_file") or "")
        built.append(target)
        if target.startswith("tests/"):
            return {"test_code": "from src.game import play\n\n\ndef test_play():\n    assert play(0) >= 0\n", "test_file": target}
        if target in _E2E_IMPL:
            source = _E2E_IMPL[target] if implement_entry or target != "src/experiment.py" else _E2E_EXPERIMENT
            return {"files": [{"filename": target, "content": source}], "summary": "impl"}
        return {"status": "PASS", "issues": []}

    log_dir = tmp_path / "logs"
    set_process_log_dir(log_dir)
    set_llm_handler(handler)
    try:
        orch = NeuroSymbolicOrchestrator(adk_root=_clone_adk_env(tmp_path), enable_layer4=False, include_docs=False, provider="mock")
        result = orch.run("Gra i eksperyment", multi_cycle_waves=True, interactive_gates=False, max_replan_retries=2)
    finally:
        set_llm_handler(None)
        set_process_log_dir(None)
    return result, built, _events(log_dir)


def test_e2e_the_entrypoint_runs_after_what_it_uses_and_every_task_sees_its_specification(tmp_path: Path):
    result, built, events = _e2e(tmp_path)
    assert result["status"] == "COMPLETED"
    assert built[:4] == ["src/config.py", "src/game.py", "src/experiment.py", "tests/test_game.py"]
    verified = {e["vertex"] for e in events if e["event"] == "VERTEX_STATE" and e["state"] == "verified"}
    assert {"src/config.py", "src/game.py", "src/experiment.py"} <= verified


def test_e2e_an_unimplemented_entrypoint_never_completes_the_run(tmp_path: Path):
    """01: the entrypoint stayed `raise NotImplementedError` for the whole run."""
    result, _built, events = _e2e(tmp_path, implement_entry=False)
    assert result["status"] != "COMPLETED"
    assert any(e["event"] == "VERDICT" and "NOT_IMPLEMENTED" in str(e.get("first_issue")) for e in events)
