"""§XV (benchmarks of 2026-11-20): what the planner sees, false plan blockers, the culprit of a failed experiment
run, the categories evolution learns from, typos in tests, patches of modules that import one another, and the
published code bundle."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph.validate import code_violations
from adk.orchestration.common import available_package_imports
from adk.orchestration.failure_kinds import _issue_category
from adk.orchestration.failure_attribution import _traceback_culprit
from adk.orchestration.plan_change import _typos

from adk.orchestration.planning import _existing_code
from adk.tools.building.output_bundle import organize_benchmark_output_bundle
from tests.test_plan_stages import _MOD_A, _base_plan, _make_orch


def test_categories_evolution_can_learn_from() -> None:
    """E2: concise ruff findings and experiment tracebacks fell into `generic`."""
    assert _issue_category(["Ruff lint failure: src\\experiment_runner.py:35:20: F821 Undefined name `config`"]) == "F821"
    trace = 'Traceback (most recent call last):\n  File "x.py", line 1, in <module>\nTypeError: boxplot() got labels'
    assert _issue_category([trace]) == "run:TypeError"
    assert _issue_category(["something nobody recognises"]) == "generic"


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


def test_a_test_typo_is_not_an_interface_gap() -> None:
    """E3: `no_std` read by a test became an alias of `noise_std` in the interface."""
    interface = "class SyntheticDataset:\n    def __init__(self, noise_std: float) -> None:\n        self.noise_std = noise_std\n"
    issue = ("TEST_OUTSIDE_SPEC [tests/test_data.py]: reads SyntheticDataset.no_std, which the interface does not "
             "declare (test only declared methods and attributes)")
    assert _typos([issue], interface) == ["SyntheticDataset.no_std (did you mean `noise_std`?)"]
    assert _typos([issue.replace("no_std", "colour")], interface) == []


def test_the_planner_sees_the_environment_and_existing_code(tmp_path: Path) -> None:
    """P1/P2: 04 planned on an absent torch; 03 never saw the baseline its prompt asked it to keep."""
    (tmp_path / "core.py").write_text("def search() -> int:\n    return 1\n", encoding="utf-8")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "noise.py").write_text("x = 1\n", encoding="utf-8")
    assert _existing_code(tmp_path) == {"core.py": "def search() -> int:\n    return 1\n"}
    assert "np" in available_package_imports()


def test_existing_code_is_kept_instead_of_its_stub(tmp_path: Path) -> None:
    """P2: declaring the brownfield baseline in `interfaces` would have overwritten it with a stub."""
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    existing = orch.workspace_dir / "src" / "mod_a.py"
    existing.parent.mkdir(parents=True)
    existing.write_text(_MOD_A, encoding="utf-8")
    tasks = [{"task_id": "T1", "target_node": "src/mod_b.py", "description": "Implement helper_b"}]
    blueprint = {**plan["academic_blueprint"], "entrypoint": plan["entrypoint"], "plots": plan["plots"]}
    h = orch._build_project_hypergraph(plan["interfaces"], blueprint, tasks)
    assert existing.read_text(encoding="utf-8") == _MOD_A
    assert h.vertices["src/mod_a.py"].state == "verified"
    assert "NotImplementedError" in (orch.workspace_dir / "src" / "mod_b.py").read_text(encoding="utf-8")


def test_the_published_bundle_keeps_package_code(tmp_path: Path) -> None:
    """R1: only root files were copied, so 02's `code/` was empty while its code sat in `src/`."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "detector.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "main_entry.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "evolved_adk" / "tools").mkdir(parents=True)
    (tmp_path / "evolved_adk" / "tools" / "t.py").write_text("z = 3\n", encoding="utf-8")
    organize_benchmark_output_bundle(tmp_path)
    assert (tmp_path / "code" / "src" / "detector.py").is_file()
    assert (tmp_path / "code" / "main_entry.py").is_file()
    assert not (tmp_path / "src").exists()
    assert (tmp_path / "evolved_adk" / "tools" / "t.py").is_file()


# --- contradictions code / prompt / task (2026-11-21) -------------------------------------------------------------

def test_results_contract_is_enforced_not_only_prompted(tmp_path: Path) -> None:
    """K5: 02 wrote a row per seed with a `seed` column; `method+metric` pointers then cited the first seed."""
    from adk.orchestration.building import _results_format_problem

    good = tmp_path / "good.csv"
    good.write_text("method,metric,value,std_dev,n_runs\nensemble,f1,0.8,0.1,5\nzscore,f1,0.7,0.1,5\n", encoding="utf-8")
    per_seed = tmp_path / "per_seed.csv"
    per_seed.write_text("method,metric,value,seed\nzscore,f1,0.7,42\nzscore,f1,0.6,43\n", encoding="utf-8")
    assert _results_format_problem(good) == "" and _results_format_problem(tmp_path / "absent.csv") == ""
    problem = _results_format_problem(per_seed)
    assert "seed" in problem and "zscore+f1" in problem


def test_only_an_unmeasured_declared_metric_blocks(tmp_path: Path) -> None:
    """K6: a measured but undeclared metric blocked the final gate although documented as non-blocking; `F1` ≠ `f1`."""
    from adk.orchestration import agent_texts as texts
    from adk.orchestration.common import _declared_vs_measured_metrics

    (tmp_path / "results.csv").write_text("method,metric,value\na,f1,1\na,auc,1\n", encoding="utf-8")
    findings = _declared_vs_measured_metrics(["F1", "recall"], tmp_path)
    assert texts.metric_not_measured("F1") not in findings
    assert texts.metric_not_measured("recall") in findings and texts.metric_not_declared("auc") in findings


def test_the_experiment_time_limit_reaches_planner_and_coder() -> None:
    """K3: the harness stopped the experiment after 180 s, and no prompt or payload said so."""
    import inspect

    from adk.orchestration import context, planning
    from adk.tools.building.experiment_runner import EXPERIMENT_TIMEOUT_S, execute_workspace_experiment

    assert inspect.signature(execute_workspace_experiment).parameters["timeout"].default == EXPERIMENT_TIMEOUT_S
    assert "experiment_time_limit_s" in inspect.getsource(planning) and "time_limit_s" in inspect.getsource(context)
    planners = [Path(f"adk/agents/planning/{md}.md").read_text(encoding="utf-8") for md in ("plan_outline", "plan_module")]
    coder = Path("adk/agents/building/seed_coder.md").read_text(encoding="utf-8")
    assert all("experiment_time_limit_s" in planner for planner in planners) and "experiment.time_limit_s" in coder


def test_a_subsection_heading_in_the_title_does_not_replace_the_chapter(tmp_path: Path) -> None:
    """02: the discoverer's `section_title` was `Rozdział 2: …\n### 2.2 …`; chapter 2 of T2 (2582 characters) was lost."""
    orch = _make_orch(tmp_path)
    orch.include_docs = True
    title = "Rozdział 2: Przegląd literatury"
    orch._materialize_workspace_artifact("thesis.md", {
        "research_stage": "background", "section_title": title, "literature_review_section": "Tło problemu."}, writer={})
    orch._materialize_workspace_artifact("thesis.md", {
        "research_stage": "discoverer", "section_title": f"{title}\n### 2.2 Najnowsze prace",
        "literature_review_section": "Nowe metody."}, writer={})
    text = (orch.workspace_dir / "thesis.md").read_text(encoding="utf-8")
    assert "Tło problemu." in text and "### 2.2 Najnowsze prace" in text and "Nowe metody." in text


def test_each_module_the_entrypoint_skips_is_its_own_finding() -> None:
    """02: one finding listing five modules; importing four of them changed its text and the patch was rejected."""
    lib = "def f() -> int:\n    ...\n"
    entry = "from a import f\n\ndef run() -> None:\n    ...\n"
    found = [str(v) for v in code_violations({"a.py": lib, "b.py": lib, "c.py": lib, "run.py": entry}, "run.py:run", "")[1]
             if "ENTRYPOINT_DOES_NOT_USE" in str(v)]
    assert len(found) == 2 and any("b.py" in f for f in found) and any("c.py" in f for f in found)


def test_an_imported_existing_module_joins_the_plan_with_its_own_source() -> None:
    """03: the plan imported the baseline `core` without declaring it; three patches failed on "neither planned nor
    installed". Existing code is its own specification, and what it imports comes along (`core` -> `config`)."""
    from adk.benchmarks.inputs import PATHFINDING_BASELINE_CONFIG_CODE, PATHFINDING_BASELINE_CORE_CODE
    from adk.orchestration.plan_existing import _with_existing

    existing = {"core.py": PATHFINDING_BASELINE_CORE_CODE, "config.py": PATHFINDING_BASELINE_CONFIG_CODE, "unused.py": "x = 1\n"}
    plan = {"interfaces": {"run.py": "from core import search_grid\n\ndef run() -> None:\n    ...\n"}}
    merged = _with_existing(plan, existing)["interfaces"]
    assert set(merged) == {"run.py", "core.py", "config.py"} and merged["core.py"] == PATHFINDING_BASELINE_CORE_CODE
    assert _with_existing(plan, {}) is plan


def test_a_failed_model_call_is_an_answer_not_a_crash() -> None:
    """01: one planner call exceeded the HTTP timeout and the whole run crashed (CRASHED: timed out). Ten places
    called the model with no guard; `call_agent` now returns the failure, so every one of them goes on."""
    from adk.core.llm import call_agent, set_llm_handler

    def hung(*_a):
        raise TimeoutError("wall clock")

    set_llm_handler(hung)
    try:
        for md in ("task_planner", "plan_module", "seed_coder"):
            folder = "building" if md == "seed_coder" else "planning"
            res = call_agent(f"agents/{folder}/{md}.md", {}, model_tier="LRM", provider="mock")
            assert res["status"] == "error" and res["output"] == {} and "wall clock" in res["error"]

        def broken(*_a):
            raise ValueError("a bug is not a transport failure")

        set_llm_handler(broken)
        try:
            call_agent("agents/planning/plan_module.md", {}, model_tier="LRM", provider="mock")
        except ValueError:
            pass
        else:
            raise AssertionError("a programming error must not be swallowed")
    finally:
        set_llm_handler(None)


def test_an_undefined_name_gets_its_import_line_as_a_hint(tmp_path: Path) -> None:
    """F821 `pd`, `plot_results`, `src` failed six tasks after three repairs each with no hint. D2 (2026-11-14):
    the harness inserts nothing; the author gets the one import line from the source of truth."""
    from types import SimpleNamespace

    from adk.orchestration.findings import repair_findings
    from adk.orchestration.import_hints import importable_names

    edge = SimpleNamespace(type="I", id="I:src/plots.py", spec={"import": "src.plots", "symbols": {"plot_results": {"kind": "func"}}})
    h = SimpleNamespace(edges={edge.id: edge})
    source = "def run():\n    plot_results(pd)\n    src.plots.plot_results()\n    mystery()\n"
    (tmp_path / "experiment.py").write_text(source, encoding="utf-8")
    issue = (
        "Ruff lint failure: experiment.py:2:5: F821 Undefined name `plot_results`\nexperiment.py:2:18: F821 Undefined name `pd`\n"
        "experiment.py:3:5: F821 Undefined name `src`\nexperiment.py:4:5: F821 Undefined name `mystery`"
    )
    texts = [f.text for f in repair_findings([issue], tmp_path, lambda rel: importable_names(h, rel, available_package_imports()))]
    assert "`from src.plots import plot_results`" in texts[0] and "`import pandas as pd`" in texts[1]
    assert "`import src.plots`" in texts[2] and "import line" not in texts[3]
    assert (tmp_path / "experiment.py").read_text(encoding="utf-8") == source  # nothing inserted


def test_a_stub_finding_names_the_functions() -> None:
    """01 game_env: "a function still only raises NotImplementedError" three times, never which one."""
    from adk.hypergraph.oracles import stub_functions

    source = "class Env:\n    def reset(self):\n        raise NotImplementedError\n    def step(self):\n        return 1\n\ndef helper():\n    ...\n"
    assert sorted(stub_functions(source)) == ["Env.reset", "helper"]


def test_a_test_may_read_what_a_function_returns() -> None:
    """02: `mask = get_ground_truth_mask(...); mask.shape` rejected the tester four times as undeclared API."""
    from types import SimpleNamespace

    from adk.hypergraph.observe import _test_diff

    symbols = {"get_ground_truth_mask": {"kind": "func"}, "Model": {"kind": "class"}}
    h = SimpleNamespace(edges={"I:gen.py": SimpleNamespace(spec={"symbols": symbols})})
    seen = {"attrs_used": [("gen.py", "get_ground_truth_mask", "shape"), ("gen.py", "Model", "secret")]}
    found = _test_diff("tests/test_gen.py", seen, h)
    assert len(found) == 1 and "Model.secret" in found[0].detail and "shape" not in found[0].detail


def test_a_citation_the_bibliography_lacks_never_enters_the_thesis(tmp_path: Path) -> None:
    """03: `dijkstra1959` stayed in the document after its task failed and failed every later section (2 -> 21 errors)."""
    orch = _make_orch(tmp_path)
    (orch.workspace_dir / "references.bib").write_text("@article{tang2026scaling,\n title={X}\n}\n", encoding="utf-8")
    text = orch._known_citations_only(r"Dijkstra~\cite{dijkstra1959}. Scaling \cite{tang2026scaling, wah2016}.")
    assert text == r"Dijkstra. Scaling \cite{tang2026scaling}."


def test_an_answer_that_is_no_json_is_told_so() -> None:
    """01/02: a cut-off answer was told its fields ['error', 'issues', 'raw_response'] match no shape."""
    from adk.orchestration import agent_texts as texts

    assert "not valid JSON" in texts.unknown_answer_shape("src/a.py", ["error", "issues", "raw_response"], {})
