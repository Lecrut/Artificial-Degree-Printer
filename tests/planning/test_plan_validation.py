"""A plan that cannot work is rejected before any code is written: by code first (entrypoint, plots, undeclared uses, packages, the results contract), then by the critic."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph import code_violations, load
from adk.orchestration.plan_interfaces import _plan_interfaces
from tests.support.sample_research_project import (
    _CONFIG,
    _ENTRY,
    _EXPERIMENT_IFACE,
    _GENERATOR,
    _GOOD,
    _rules,
)
from tests.support.tictactoe_interface import ENV_INTERFACE


def _plan_of(interfaces: dict) -> dict:
    return {"interfaces": interfaces, "entrypoint": _ENTRY, "plots": _ENTRY,
            "academic_blueprint": {"metrics": ["f1"], "planned_chapters": [{"index": 1, "title": "Wstęp"}]}}


_AGENT = (
    '"""Agent."""\nfrom src.config import CHANNELS\n\n\n'
    "class QAgent:\n"
    '    """Q-learning agent."""\n\n'
    "    def __init__(self, lr: float) -> None:\n"
    '        """Store the learning rate."""\n        self.lr = lr\n\n'
    "    def learn(self, state: tuple, next_state: tuple) -> None:\n"
    '        """Update the table from one transition."""\n\n'
    "    def reset(self) -> tuple:\n"
    '        """Empty board: nine zeros."""\n'
)


def test_a_valid_plan_has_no_violations():
    specs, violations = code_violations(_GOOD, _ENTRY)
    assert violations == []
    assert specs["src/config.py"]["symbols"]["SEEDS"] == {"kind": "const", "type": "list[int]"}
    assert specs["src/experiment.py"]["uses"] == {"src/config.py": ["CHANNELS", "N_REPETITIONS", "SEEDS"], "src/data_generator.py": ["generate_sample"]}


def test_the_plans_of_01_and_02_are_rejected_before_any_code():
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


def test_undeclared_uses_duplicate_modules_and_missing_packages_are_violations():
    uses_missing = {**_GOOD, "src/experiment.py": _EXPERIMENT_IFACE.replace("SEEDS", "SEED_VALUE")}
    assert "USES_UNDECLARED" in _rules(code_violations(uses_missing, _ENTRY)[1])
    duplicate = {**_GOOD, "config.py": _CONFIG}
    assert "DUPLICATE_MODULE" in _rules(code_violations(duplicate, _ENTRY)[1])
    no_package = {**_GOOD, "src/data_generator.py": "import surely_not_installed_pkg\n" + _GENERATOR}
    assert "PACKAGE_UNAVAILABLE" in _rules(code_violations(no_package, _ENTRY)[1])


def test_planning_returns_violations_to_the_planner_then_builds_h_and_stubs(tmp_path: Path):
    """The module whose interface the code rejects goes back to its author alone (§XVI); then H and the stubs."""
    from adk.mocks.staged import sketch_of
    from adk.orchestration.plan_sketch import sketch_to_source
    from tests.support.orchestrator_sandbox import _orch
    from tests.support.staged_planning import _run, _sketch

    orch = _orch(tmp_path)
    broken = _EXPERIMENT_IFACE.replace("run_experiment()", "run_experiment(config)")
    reviewed: list[dict] = []

    def module(payload, _n):
        return _sketch(broken) if payload["module"]["file"] == "src/experiment.py" and "feedback" not in payload else None

    def critic(payload, _n):
        reviewed.append(payload)
        return None

    (plan, interfaces, violations), calls = _run(orch, _plan_of(_GOOD), {"plan_module": module, "plan_critic_guard": critic})
    sent = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/experiment.py"]
    # What the plan keeps is what the authors declared: their sketches, built into interfaces with every body `...`.
    assert violations == [] and interfaces == {rel: sketch_to_source(sketch_of(src)) for rel, src in _GOOD.items()} and len(sent) == 2
    assert any("ENTRYPOINT_HAS_ARGUMENTS" in f for f in sent[1]["feedback"]) and "config" in sent[1]["previous_sketch"]["functions"][0]["signature"]
    # The main critic judges only the plan the code accepted, and sees its interfaces (stubs: no written bodies).
    from adk.orchestration.interface_view import interface_view
    assert len(reviewed) == 1 and reviewed[0]["interfaces"] == {rel: interface_view(src) for rel, src in interfaces.items()}

    h = orch._build_project_hypergraph(interfaces, {"entrypoint": _ENTRY, "metrics": ["f1"]}, plan["tasks"])
    assert h is not None and load(orch.hypergraph_path).edges.keys() == h.edges.keys()
    stub = (orch.workspace_dir / "src/experiment.py").read_text(encoding="utf-8")
    assert "raise NotImplementedError" in stub


def test_a_plan_still_broken_after_its_corrections_stops_the_run(tmp_path: Path):
    from tests.support.orchestrator_sandbox import _orch
    from tests.support.staged_planning import _run, _sketch

    orch = _orch(tmp_path)
    broken = _GENERATOR.replace("-> list[float]", "-> List[float]")

    def module(payload, _n):
        return _sketch(broken) if payload["module"]["file"] == "src/data_generator.py" else None

    (_, _, violations), _calls = _run(orch, _plan_of(_GOOD), {"plan_module": module})
    assert any("STUB_DOES_NOT_IMPORT" in v for v in violations)
    assert orch._plan_rejected(violations, [])["stop"]["status"] == "PLAN_REJECTED"


def test_entrypoint_that_never_imports_a_planned_module_is_rejected():
    """01: run_experiment in config.py imported nothing; the coder rewrote the game inside it (83x DATA_FAILED)."""
    plan = {**_GOOD, "src/agent.py": _AGENT}
    found = [v for v in code_violations(plan, _ENTRY)[1] if v.rule == "ENTRYPOINT_DOES_NOT_USE"]
    assert len(found) == 1 and "src/agent.py" in found[0].detail and found[0].culprit == "src/experiment.py"


def test_declared_plots_module_is_not_required_to_be_imported_by_the_experiment():
    """§XIII F2: the figures module is whatever the plan declares in `plots`, not a fixed name or symbol."""
    plots = '"""Plots."""\n\n\ndef draw() -> None:\n    """Write the figures."""\n'
    interfaces = {**_GOOD, "viz/figs.py": plots}
    assert "ENTRYPOINT_DOES_NOT_USE" not in _rules(code_violations(interfaces, _ENTRY, "viz/figs.py:draw")[1])
    assert "ENTRYPOINT_DOES_NOT_USE" in _rules(code_violations(interfaces, _ENTRY)[1])
    assert "PLOTS_NOT_DECLARED" in _rules(code_violations(interfaces, _ENTRY, "viz/figs.py:plot")[1])
    with_args = plots.replace("def draw()", "def draw(out: str)")
    assert "PLOTS_HAS_ARGUMENTS" in _rules(code_violations({**_GOOD, "viz/figs.py": with_args}, _ENTRY, "viz/figs.py:draw")[1])


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


def test_each_module_the_entrypoint_skips_is_its_own_finding() -> None:
    """02: one finding listing five modules; importing four of them changed its text and the patch was rejected."""
    lib = "def f() -> int:\n    ...\n"
    entry = "from a import f\n\ndef run() -> None:\n    ...\n"
    found = [str(v) for v in code_violations({"a.py": lib, "b.py": lib, "c.py": lib, "run.py": entry}, "run.py:run", "")[1]
             if "ENTRYPOINT_DOES_NOT_USE" in str(v)]
    assert len(found) == 2 and any("b.py" in f for f in found) and any("c.py" in f for f in found)


def test_plan_interfaces_accept_a_list_and_drop_tests_and_unparsable_code() -> None:
    found = _plan_interfaces(
        {
            "interfaces": [
                {"file": "./src/env.py", "source": ENV_INTERFACE},
                {"file": "tests/test_env.py", "source": "def test_x(): ..."},
                {"file": "src/bad.py", "source": "def f(:"},
            ]
        }
    )
    assert list(found) == ["src/env.py"]
