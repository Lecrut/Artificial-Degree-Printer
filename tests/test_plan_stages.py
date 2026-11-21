"""§XVI: planning in stages. The outline, each module's interface and the whole plan are checked separately; a
finding reopens only the part it names, the plan grows and never goes back to the start."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from adk.mocks.staged import outline_from_plan, staged_answer
from adk.orchestration import plan_stages
from adk.orchestration.plan_outline import module_order, outline_of, outline_violations
from adk.orchestration.plan_tasks import planned_tasks
from adk.orchestrator import NeuroSymbolicOrchestrator


def _make_orch(tmp_path: Path) -> NeuroSymbolicOrchestrator:
    orch = NeuroSymbolicOrchestrator(adk_root="adk", enable_layer4=False, provider="mock")
    orch.workspace_dir = tmp_path / "workspace"
    orch.state_dir = tmp_path / "state"
    orch.workspace_dir.mkdir(parents=True, exist_ok=True)
    orch.state_dir.mkdir(parents=True, exist_ok=True)
    orch.task_queue_path = orch.state_dir / "task_queue.json"
    orch.validation_report_path = orch.state_dir / "validation_report.json"
    orch.blueprint_path = orch.state_dir / "academic_blueprint.json"
    orch.failure_ledger_path = orch.state_dir / "failure_ledger.json"
    orch.hitl_flag_path = orch.state_dir / "hitl_flag.json"
    orch.evolution_history_path = orch.state_dir / "evolution_history.json"
    return orch


_MOD_A = 'def helper_a() -> int:\n    """Return 1."""\n    return 1\n'
_MOD_B = 'from src.mod_a import helper_a\n\n\ndef helper_b() -> int:\n    """Return 2."""\n    return 2\n'
_EXP = (
    "from src.mod_a import helper_a\n"
    "from src.mod_b import helper_b\n\n"
    'def run_experiment() -> int:\n    """Run."""\n    return helper_a() + helper_b()\n'
)
_PLOTS = 'def plots() -> None:\n    """Figures."""\n'
_ENTRY = "src/experiment.py:run_experiment"


def _base_plan() -> dict:
    return {
        "interfaces": {"src/mod_a.py": _MOD_A, "src/mod_b.py": _MOD_B, "src/experiment.py": _EXP, "src/figures.py": _PLOTS},
        "entrypoint": _ENTRY,
        "plots": "src/figures.py:plots",
        "academic_blueprint": {
            "thesis_statement": "A+B=3", "metrics": ["score"],
            "planned_chapters": [{"index": 1, "title": "Wstęp"}, {"index": 2, "title": "Wyniki eksperymentu"}],
        },
    }


Answer = Callable[[dict[str, Any], int], Any]


def _run(orch: NeuroSymbolicOrchestrator, plan: dict, overrides: dict[str, Answer] | None = None) -> tuple[Any, list[tuple[str, dict]]]:
    """`_staged_plan` with the planning agents answering `plan` stage by stage, except the `overrides` (agent ->
    f(payload, call number of that agent)). Returns (result, calls as (agent, payload))."""
    calls: list[tuple[str, dict]] = []

    def fake(md: Any, payload: dict, **_kw: Any) -> dict:
        agent = Path(md).stem
        calls.append((agent, payload))
        n = sum(1 for a, _ in calls if a == agent)
        if overrides and agent in overrides:
            out = overrides[agent](payload, n)
            if isinstance(out, BaseException):  # a failed call: `call_agent` returns it as an answer
                return {"status": "error", "error": str(out), "output": {}}
            if out is not None:
                return {"status": "ok", "output": out}
        return {"status": "ok", "output": staged_answer(plan, agent, payload)}

    orch._call_agent = fake
    orch._events_from = len(_lines(orch))  # the log is shared by the test session
    return orch._staged_plan({"user_prompt": "p", "detected_template": {"thesis_type": "inzynierska", "is_certain": True}}), calls


def _lines(orch: NeuroSymbolicOrchestrator) -> list[str]:
    return orch.logger.events_path.read_text(encoding="utf-8").splitlines() if orch.logger.events_path.exists() else []


def _events(orch: NeuroSymbolicOrchestrator, *kinds: str) -> list[dict]:
    lines = _lines(orch)[getattr(orch, "_events_from", 0):]
    return [e for e in map(json.loads, lines) if not kinds or e["event"] in kinds]


def _module_calls(calls: list[tuple[str, dict]]) -> list[str]:
    return [p["module"]["file"] for a, p in calls if a == "plan_module"]


def _critic_fail(where: str) -> dict:
    return {"status": "FAIL", "issues": [{"blocking": True, "category": "interfaces", "where": where, "problem": "broken", "fix": "fix it"}]}


# --- stage 1: the outline ----------------------------------------------------------------------------------------


def test_the_outline_is_checked_by_code() -> None:
    outline = outline_of(outline_from_plan(_base_plan()))
    assert outline_violations(outline, {}, True) == []
    broken = outline_of({**outline_from_plan(_base_plan()), "plots": "src/figures.py:draw"})
    broken["modules"].append({"file": "src/extra.py", "purpose": "x", "depends_on": ["src/ghost.py"], "provides": ["f"]})
    broken["modules"][0]["depends_on"] = ["src/mod_b.py"]  # mod_a <-> mod_b
    found = outline_violations(broken, {}, True)
    assert any("OUTLINE [src/extra.py]: depends on src/ghost.py" in f for f in found)
    assert any("cycle" in f and "src/mod_a.py" in f for f in found)
    assert any(f.startswith("OUTLINE [plots]") and "provides" in f for f in found)
    assert not any("[src/extra.py]: the experiment" in f for f in found)  # reachability is not judged on a cycle
    no_metrics = outline_of({**outline_from_plan(_base_plan()), "academic_blueprint": {"planned_chapters": [{"index": 1}]}})
    assert any("metrics" in f for f in outline_violations(no_metrics, {}, True))


def test_dependencies_come_first_and_the_experiment_last() -> None:
    outline = outline_of(outline_from_plan(_base_plan()))
    order = module_order(outline)
    assert order[-1] == "src/experiment.py" and order.index("src/mod_a.py") < order.index("src/mod_b.py")


def test_an_outline_problem_goes_back_to_the_outline_author(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    plan = _base_plan()

    def outline(payload: dict, n: int) -> dict | None:
        if n == 1:
            first = outline_from_plan(plan)
            first["modules"].append({"file": "src/unused.py", "purpose": "x", "depends_on": [], "provides": ["f"]})
            return first
        assert any("OUTLINE [src/unused.py]" in f for f in payload["feedback"]) and payload["current_outline"]
        return None

    (out, _, blockers), calls = _run(orch, plan, {"plan_outline": outline})
    assert blockers == [] and "src/unused.py" not in out["interfaces"]
    assert [a for a, _ in calls].count("plan_outline") == 2


# --- stage 2: the interfaces ------------------------------------------------------------------------------------


def test_a_plan_is_built_module_by_module_and_fused(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (out, interfaces, blockers), calls = _run(orch, _base_plan())
    assert blockers == [] and set(interfaces) == set(_base_plan()["interfaces"])
    assert _module_calls(calls)[-1] == "src/experiment.py"
    mod_b_payload = next(p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_b.py")
    assert set(mod_b_payload["dependencies"]) == {"src/mod_a.py"}  # it sees what it builds on, accepted
    assert [c["file"] for c in mod_b_payload["consumers"]] == ["src/experiment.py"]
    kinds = [e["event"] for e in _events(orch) if e["event"].startswith("PLAN_")]
    assert kinds.index("PLAN_OUTLINE_ACCEPTED") < kinds.index("PLAN_MODULE_ACCEPTED") < kinds.index("PLAN_FUSED") < kinds.index("PLAN_CHECKED")


def test_a_module_is_corrected_alone_and_the_others_stay_frozen(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    broken = _MOD_B.replace("import helper_a", "import helper_z")

    def module(payload: dict, _n: int) -> dict | None:
        if payload["module"]["file"] == "src/mod_b.py" and "feedback" not in payload:
            return {"source": broken}
        return None

    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    assert blockers == []
    assert _module_calls(calls).count("src/mod_a.py") == 1 and _module_calls(calls).count("src/mod_b.py") == 2
    retry = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_b.py"][1]
    assert retry["previous_source"] == broken and any("USES_UNDECLARED" in f for f in retry["feedback"])


def test_a_module_critic_blocks_once_then_the_corrected_module_is_accepted(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)

    def critic(payload: dict, _n: int) -> dict | None:
        return _critic_fail("src/mod_a.py:helper_a") if payload["module"]["file"] == "src/mod_a.py" else None

    (_, _, blockers), calls = _run(orch, _base_plan(), {"module_critic_guard": critic})
    assert blockers == [] and _module_calls(calls).count("src/mod_a.py") == 2
    assert [a for a, p in calls if a == "module_critic_guard" and p["module"]["file"] == "src/mod_a.py"] == ["module_critic_guard"]
    accepted = next(e for e in _events(orch, "PLAN_MODULE_ACCEPTED") if e["module"] == "src/mod_a.py")
    assert accepted["over_critic"]  # the objection stays in the log


def test_a_module_may_ask_its_dependency_for_more(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    exp_c = _EXP.replace("import helper_a", "import helper_a, helper_c")

    def module(payload: dict, _n: int) -> dict | None:
        rel = payload["module"]["file"]
        if rel == "src/experiment.py" and not any("helper_c" in s for s in payload["dependencies"].values()):
            return {"source": exp_c, "needs": {"src/mod_a.py": "helper_c() -> int"}}
        if rel == "src/mod_a.py" and any("helper_c" in f for f in payload.get("feedback") or []):
            return {"source": _MOD_A + '\n\ndef helper_c() -> int:\n    """Return 3."""\n    return 3\n'}
        if rel == "src/experiment.py":
            return {"source": exp_c}
        return None

    (_, interfaces, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    assert blockers == [] and "helper_c" in interfaces["src/mod_a.py"] and "helper_c" in interfaces["src/experiment.py"]
    assert _module_calls(calls).count("src/mod_b.py") == 1  # untouched by the extension of mod_a
    assert _events(orch, "PLAN_MODULE_NEEDS")[0]["needs"] == {"src/mod_a.py": "helper_c() -> int"}


def test_a_module_that_cannot_converge_escalates_once_to_the_outline(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)

    def module(payload: dict, _n: int) -> dict | None:
        return {"source": "def helper_b(:\n"} if payload["module"]["file"] == "src/mod_b.py" else None

    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    assert blockers and "INTERFACE_DOES_NOT_PARSE" in blockers[0]
    revisions = [p for a, p in calls if a == "plan_outline" and "current_outline" in p]
    assert len(revisions) == 1 and "OUTLINE [src/mod_b.py]: this module could not be designed" in revisions[0]["feedback"][0]


def test_a_timed_out_call_is_a_failed_round_not_a_crash(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)

    def module(payload: dict, n: int) -> Any:
        return TimeoutError("slow") if payload["module"]["file"] == "src/mod_a.py" and n == 1 else None

    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    assert blockers == [] and _module_calls(calls).count("src/mod_a.py") == 2
    retry = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_a.py"][1]
    assert "no `source`" in retry["feedback"][0]


# --- stage 4: the main critic -----------------------------------------------------------------------------------


def test_a_main_critic_finding_on_a_module_reopens_only_that_module(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_critic_guard": lambda _p, n: _critic_fail("src/mod_b.py:helper_b") if n == 1 else None})
    assert blockers == []
    modules = _module_calls(calls)
    assert modules.count("src/mod_b.py") == 2 and modules.count("src/mod_a.py") == 1 and modules.count("src/experiment.py") == 1
    reopened = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_b.py"][1]
    assert "previous_source" in reopened and any("PLAN_CRITIC [src/mod_b.py:helper_b]" in f for f in reopened["feedback"])


def test_a_main_critic_finding_on_the_outline_keeps_the_unchanged_modules(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    plan = _base_plan()

    def outline(payload: dict, _n: int) -> dict | None:
        if "current_outline" not in payload:
            return None
        revised = json.loads(json.dumps(payload["current_outline"]))
        revised["academic_blueprint"]["metrics"] = ["score", "time"]
        return revised

    (out, _, blockers), calls = _run(orch, plan, {
        "plan_critic_guard": lambda _p, n: _critic_fail("academic_blueprint.metrics") if n == 1 else None,
        "plan_outline": outline,
    })
    assert blockers == [] and out["academic_blueprint"]["metrics"] == ["score", "time"]
    assert len(_module_calls(calls)) == 4  # every module designed once: nothing went back to the start


def test_an_outline_revision_reopens_only_the_modules_it_changes(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)

    def outline(payload: dict, _n: int) -> dict | None:
        if "current_outline" not in payload:
            return None
        revised = json.loads(json.dumps(payload["current_outline"]))
        next(m for m in revised["modules"] if m["file"] == "src/mod_b.py")["purpose"] = "a sharper purpose"
        return revised

    (_, _, blockers), calls = _run(orch, _base_plan(), {
        "plan_critic_guard": lambda _p, n: _critic_fail("modules") if n == 1 else None,
        "plan_outline": outline,
    })
    assert blockers == [] and _module_calls(calls).count("src/mod_b.py") == 2 and _module_calls(calls).count("src/mod_a.py") == 1
    assert _events(orch, "PLAN_OUTLINE_REVISED")[0]["changed"] == ["src/mod_b.py"]


def test_after_its_rounds_the_main_critic_cannot_stop_an_executable_plan(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_critic_guard": lambda _p, _n: _critic_fail("src/mod_a.py")})
    assert blockers == [] and [a for a, _ in calls].count("plan_critic_guard") == plan_stages.FINAL_ROUNDS + 1
    assert _events(orch, "PLAN_ACCEPTED_OVER_CRITIC")


def test_unproven_or_doctest_findings_are_warnings(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    vague = {"status": "FAIL", "issues": [
        {"blocking": True, "where": "", "problem": "something", "fix": "x"},
        {"blocking": True, "category": "doctest", "where": "src/mod_a.py", "problem": "1 != 2", "fix": "use 2"},
    ]}
    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_critic_guard": lambda _p, _n: vague})
    assert blockers == [] and [a for a, _ in calls].count("plan_critic_guard") == 1
    assert len(_events(orch, "PLAN_REVIEWED")[0]["warnings"]) == 2


def test_the_main_critic_is_not_asked_while_code_rejects_the_plan(tmp_path: Path) -> None:
    """Fusion re-checks the whole plan by code first; a finding with a culprit goes to that module."""
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    asked: list[str] = []

    def module(payload: dict, _n: int) -> dict | None:
        asked.append(payload["module"]["file"])
        return None

    original = plan_stages.code_violations
    seen = {"fusion": 0}

    def code_violations(interfaces: dict, entry: Any, plots: Any = None) -> Any:
        specs, found = original(interfaces, entry, plots)
        if seen["fusion"] == 0 and _events(orch, "PLAN_FUSED"):  # the first check of the fused plan
            from adk.hypergraph.model import Violation

            seen["fusion"] += 1
            return specs, [*found, Violation("SOMETHING_ACROSS", "only the whole plan shows it", "src/mod_b.py", "src/mod_b.py")]
        return specs, found

    plan_stages.code_violations = code_violations
    try:
        (_, _, blockers), calls = _run(orch, plan, {"plan_module": module})
    finally:
        plan_stages.code_violations = original
    assert blockers == [] and asked.count("src/mod_b.py") == 2
    assert [e["blockers"]["critic"] for e in _events(orch, "PLAN_CHECKED")][0] == []  # no critic on a rejected plan


def test_an_unreadable_critic_answer_blocks_nothing_and_is_logged(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_critic_guard": lambda _p, _n: {"answer": "looks fine"}})
    assert blockers == [] and [a for a, _ in calls].count("plan_critic_guard") == 1
    assert _events(orch, "PLAN_REVIEW_NO_VERDICT")


def test_a_models_loose_answers_are_read_as_what_they_mean() -> None:
    from adk.orchestration.plan_stages import _module_source

    loose = outline_of({
        "modules": {"src/a.py": {"purpose": "p", "depends_on": "src/b.py", "provides": "f"}, "src/b.py": {"purpose": "q"}},
        "entrypoint": "src/a.py:f", "plots": "src/b.py:g",
    })
    assert loose["modules"][0] == {"file": "src/a.py", "purpose": "p", "depends_on": ["src/b.py"], "provides": ["f"]}
    assert outline_of({"modules": "none"}) is None and outline_of({"modules": ["src/a.py"]})["modules"] == []
    assert _module_source({"source": "```python\nX: int = 1\n```"}, "a.py") == "X: int = 1"
    assert _module_source({"source": "X: int = 1\\nY: int = 2\\n"}, "a.py") == "X: int = 1\nY: int = 2\n"
    assert _module_source({"interfaces": {"a.py": "X: int = 1\n"}}, "a.py") == "X: int = 1\n" and _module_source({"source": "  "}, "a.py") == ""


def test_the_author_sees_an_existing_dependency_the_outline_does_not_plan(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "mod_a.py").write_text(_MOD_A, encoding="utf-8")
    plan = _base_plan()

    def outline(_payload: dict, n: int) -> dict | None:
        if n > 1:
            return None
        first = outline_from_plan(plan)
        first["modules"] = [m for m in first["modules"] if m["file"] != "src/mod_a.py"]  # existing, listed only as a dependency
        return first

    (_, _, blockers), calls = _run(orch, plan, {"plan_outline": outline})
    mod_b = next(p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_b.py")
    assert blockers == [] and mod_b["dependencies"] == {"src/mod_a.py": _MOD_A}


def test_a_module_that_asked_for_more_is_given_its_own_draft_back(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    exp_c = _EXP.replace("import helper_a", "import helper_a, helper_c")

    def module(payload: dict, _n: int) -> dict | None:
        rel = payload["module"]["file"]
        if rel == "src/experiment.py" and "helper_c" not in " ".join(payload["dependencies"].values()):
            return {"source": exp_c, "needs": {"src/mod_a.py": "helper_c() -> int"}}
        if rel == "src/mod_a.py" and any("helper_c" in f for f in payload.get("feedback") or []):
            return {"source": _MOD_A + '\n\ndef helper_c() -> int:\n    """Return 3."""\n    return 3\n'}
        return {"source": exp_c} if rel == "src/experiment.py" else None

    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    again = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/experiment.py"][1]
    assert blockers == [] and again["previous_source"] == exp_c and "now declares what you asked for" in again["feedback"][0]


def test_the_specialist_the_caller_asked_for_implements_the_modules(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    orch.enable_layer4 = True
    plan = _base_plan()
    asked = {"user_prompt": "p", "missing_agent_specialization": "latex_formatter", "detected_template": {"thesis_type": "inzynierska", "is_certain": True}}

    def fake(md: Any, payload: dict, **_kw: Any) -> dict:
        return {"status": "ok", "output": staged_answer(plan, Path(md).stem, payload)}

    orch._call_agent = fake
    out, _, blockers = orch._staged_plan(asked)
    coders = {t["assigned_agent"] for t in out["tasks"] if t["target_node"].endswith(".py") and not t["target_node"].startswith("tests/")}
    assert blockers == [] and coders == {"latex_formatter"} and out["missing_agent_specialization"] == "latex_formatter"
    orch.enable_layer4 = False  # nobody can create it: no task is left on an agent that does not exist
    out, _, _ = orch._staged_plan(asked)
    assert {t["assigned_agent"] for t in out["tasks"] if t["target_node"] == "src/mod_a.py"} == {"seed_coder"}


def test_every_prompt_names_every_input_the_code_sends(tmp_path: Path) -> None:
    """Contracts are enforced by the payload and stated in the prompt (§XIII, §XV.8): a key the code sends an agent
    and its prompt never mentions is an input the model reads blind. A run with something to correct at every stage."""
    plan = _base_plan()

    def outline(_payload: dict, n: int) -> dict | None:
        if n == 1:
            first = outline_from_plan(plan)
            first["modules"].append({"file": "src/unused.py", "purpose": "x", "depends_on": [], "provides": ["f"]})
            return first
        return None

    def broken_once(payload: dict, _n: int) -> dict | None:
        bad = _MOD_B.replace("import helper_a", "import helper_z")
        return {"source": bad} if payload["module"]["file"] == "src/mod_b.py" and "feedback" not in payload else None

    once = {"outline_critic_guard": 0, "module_critic_guard": 0, "plan_critic_guard": 0}

    def blocking(agent: str, where: str) -> Answer:
        def answer(_payload: dict, _n: int) -> dict | None:
            once[agent] += 1
            return _critic_fail(where) if once[agent] == 1 else None
        return answer

    (_, _, blockers), calls = _run(_make_orch(tmp_path), plan, {
        "plan_outline": outline, "plan_module": broken_once, "outline_critic_guard": blocking("outline_critic_guard", "src/mod_a.py"),
        "module_critic_guard": blocking("module_critic_guard", "src/mod_a.py"), "plan_critic_guard": blocking("plan_critic_guard", "src/mod_b.py"),
    })
    assert blockers == []
    sent: dict[str, set[str]] = {}
    for agent, payload in calls:
        sent.setdefault(agent, set()).update(payload)
    assert set(sent) == {"plan_outline", "outline_critic_guard", "plan_module", "module_critic_guard", "plan_critic_guard"}
    for agent, keys in sent.items():
        prompt = Path(f"adk/agents/planning/{agent}.md").read_text(encoding="utf-8")
        assert [k for k in sorted(keys) if f"`{k}`" not in prompt] == [], agent


# --- stage 3: the tasks, and existing code ------------------------------------------------------------------------


def test_the_tasks_follow_from_the_outline_and_the_interfaces() -> None:
    plan = _base_plan()
    outline = outline_of(outline_from_plan(plan))
    tasks = planned_tasks(outline, plan["interfaces"], "inzynierska", True, set())
    targets = [(t["target_node"], t["assigned_agent"]) for t in tasks]
    assert targets[0] == ("thesis.md", "background_researcher")
    assert targets[1] == ("thesis.md", "seed_writer") and "Chapter 1" in tasks[1]["description"]
    assert ("tests/test_mod_a.py", "seed_tester") in targets and ("tests/test_mod_b.py", "seed_tester") in targets
    assert not any(t.endswith(("test_experiment.py", "test_figures.py")) for t, _ in targets)  # called by the harness
    assert targets.index(("src/mod_a.py", "seed_coder")) + 1 == targets.index(("tests/test_mod_a.py", "seed_tester"))
    assert "Chapter 2" in tasks[-1]["description"]  # results after the code
    method = {**outline, "academic_blueprint": {**outline["academic_blueprint"], "planned_chapters": [
        {"index": 1, "title": "Wstęp i cel"}, {"index": 2, "title": "Metoda i architektura"}, {"index": 3, "title": "Przegląd literatury"}]}}
    order = [" ".join(t["description"].split()[:2]) for t in planned_tasks(method, plan["interfaces"], "paper", True, set())]
    assert order[:3] == ["Literature review", "Chapter 1", "Chapter 3"] and order[-1] == "Chapter 2"  # a chapter on the method waits for the code
    assert [t["assigned_agent"] for t in planned_tasks(outline, plan["interfaces"], "magisterska", True, set())][:2] == [
        "background_researcher", "discoverer_researcher"]
    assert planned_tasks(outline, plan["interfaces"], "paper", True, set())[0]["assigned_agent"] == "discoverer_researcher"
    assert all(t["target_node"].endswith(".py") for t in planned_tasks(outline, plan["interfaces"], "paper", False, set()))


def test_existing_code_is_kept_or_extended_never_lost(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "mod_a.py").write_text(_MOD_A, encoding="utf-8")
    (out, interfaces, blockers), calls = _run(orch, _base_plan())
    assert blockers == [] and interfaces["src/mod_a.py"] == _MOD_A and "src/mod_a.py" not in _module_calls(calls)
    assert "src/mod_a.py" not in [t["target_node"] for t in out["tasks"]]

    orch = _make_orch(tmp_path / "extended")
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "mod_a.py").write_text(_MOD_A, encoding="utf-8")
    plan = _base_plan()
    plan["interfaces"]["src/mod_a.py"] = 'def helper_c() -> int:\n    """Return 3."""\n    return 3\n'  # drops helper_a
    (_, _, blockers), calls = _run(orch, plan)
    first = next(p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_a.py")
    assert first["previous_source"] == _MOD_A
    assert blockers and "the existing code defines helper_a" in " ".join(blockers)
