"""Planning in four stages: the outline, the interface of each module, the tasks derived from them and the main critic. A finding reopens only the part it names, an accepted module stays frozen, the plan never goes back to the start."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from adk.mocks.staged import outline_from_plan, staged_answer
from adk.orchestration import plan_stages
from adk.orchestration.plan_outline import module_order, outline_of, outline_violations
from adk.orchestration.plan_tasks import planned_tasks
from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.phased_orchestrator import _setup_test_orchestrator, _staged_agents
from tests.support.planned_projects import SPEC
from tests.support.staged_planning import (
    _EXP,
    _MOD_A,
    _MOD_B,
    _base_plan,
    _critic_fail,
    _lines,
    _make_orch,
    _module_calls,
    _run,
    _sketch,
)


def _events(orch: NeuroSymbolicOrchestrator, *kinds: str) -> list[dict]:
    lines = _lines(orch)[getattr(orch, "_events_from", 0):]
    return [e for e in map(json.loads, lines) if not kinds or e["event"] in kinds]


def test_an_unreadable_outline_goes_back_to_its_author_and_the_queue_is_derived(tmp_path: Path) -> None:
    """An answer with no module list (token starvation) is returned to the outline author with the reason; the
    task queue is derived from the accepted outline, never left empty (§XVI)."""
    orch = _setup_test_orchestrator(tmp_path)
    captured: list[tuple[str, dict]] = []
    plan = {**SPEC, "thesis_type": "inzynierska",
            "academic_blueprint": {"thesis_title": "Badanie RL", "metrics": ["win_rate"], "planned_chapters": [{"index": 1, "title": "Wstęp"}]}}
    starved = {"thesis_type": "inzynierska", "academic_blueprint": {"thesis_title": "Badanie RL"}}

    with patch("adk.orchestrator.call_agent", side_effect=_staged_agents(plan, captured, [starved])):
        # Stopped at gate 1, right after planning: the queue is the derived plan.
        res = orch.run("01_rl_tictactoe", multi_cycle_waves=False, gate_approval_callback=lambda *_a: False)

    assert res["status"] == "HITL_PAUSED"
    outlines = [p for a, p in captured if a == "plan_outline"]
    assert len(outlines) == 2 and any("OUTLINE [modules]" in f for f in outlines[1]["feedback"])
    saved_queue = res["tasks"]
    assert [t["target_node"] for t in saved_queue if t["target_node"].endswith(".py")] == [
        "config.py", "plot_results.py", "core.py", "tests/test_core.py"
    ]
    assert saved_queue[0]["task_id"] == "T1"


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
            return _sketch(broken)
        return None

    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    assert blockers == []
    assert _module_calls(calls).count("src/mod_a.py") == 1 and _module_calls(calls).count("src/mod_b.py") == 2
    retry = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_b.py"][1]
    assert retry["previous_sketch"]["imports"] == ["from src.mod_a import helper_z"] and any("USES_UNDECLARED" in f for f in retry["feedback"])


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
            return _sketch(exp_c, needs={"src/mod_a.py": "helper_c() -> int"})
        if rel == "src/mod_a.py" and any("helper_c" in f for f in payload.get("feedback") or []):
            return _sketch(_MOD_A + '\n\ndef helper_c() -> int:\n    """Return 3."""\n    return 3\n')
        if rel == "src/experiment.py":
            return _sketch(exp_c)
        return None

    (_, interfaces, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    assert blockers == [] and "helper_c" in interfaces["src/mod_a.py"] and "helper_c" in interfaces["src/experiment.py"]
    assert _module_calls(calls).count("src/mod_b.py") == 1  # untouched by the extension of mod_a
    assert _events(orch, "PLAN_MODULE_NEEDS")[0]["needs"] == {"src/mod_a.py": "helper_c() -> int"}


def test_a_module_that_cannot_converge_escalates_once_to_the_outline(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)

    def module(payload: dict, _n: int) -> dict | None:
        return {"functions": [{"signature": "helper_b(", "docstring": ""}]} if payload["module"]["file"] == "src/mod_b.py" else None

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
    assert "declared nothing" in retry["feedback"][0]


def test_a_main_critic_finding_on_a_module_reopens_only_that_module(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_critic_guard": lambda _p, n: _critic_fail("src/mod_b.py:helper_b") if n == 1 else None})
    assert blockers == []
    modules = _module_calls(calls)
    assert modules.count("src/mod_b.py") == 2 and modules.count("src/mod_a.py") == 1 and modules.count("src/experiment.py") == 1
    reopened = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_b.py"][1]
    assert "previous_sketch" in reopened and any("PLAN_CRITIC [src/mod_b.py:helper_b]" in f for f in reopened["feedback"])


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

    def code_violations(interfaces: dict, entry: Any, plots: Any = None, metrics: Any = None) -> Any:
        specs, found = original(interfaces, entry, plots, metrics)
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
    loose = outline_of({
        "modules": {"src/a.py": {"purpose": "p", "depends_on": "src/b.py", "provides": "f"}, "src/b.py": {"purpose": "q"}},
        "entrypoint": "src/a.py:f", "plots": "src/b.py:g",
    })
    assert loose["modules"][0] == {"file": "src/a.py", "purpose": "p", "depends_on": ["src/b.py"], "provides": ["f"]}
    assert outline_of({"modules": "none"}) is None and outline_of({"modules": ["src/a.py"]})["modules"] == []


def test_a_module_that_asked_for_more_is_given_its_own_draft_back(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    exp_c = _EXP.replace("import helper_a", "import helper_a, helper_c")

    def module(payload: dict, _n: int) -> dict | None:
        rel = payload["module"]["file"]
        if rel == "src/experiment.py" and "helper_c" not in " ".join(payload["dependencies"].values()):
            return _sketch(exp_c, needs={"src/mod_a.py": "helper_c() -> int"})
        if rel == "src/mod_a.py" and any("helper_c" in f for f in payload.get("feedback") or []):
            return _sketch(_MOD_A + '\n\ndef helper_c() -> int:\n    """Return 3."""\n    return 3\n')
        return _sketch(exp_c) if rel == "src/experiment.py" else None

    (_, _, blockers), calls = _run(orch, _base_plan(), {"plan_module": module})
    again = [p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/experiment.py"][1]
    assert blockers == [] and again["previous_sketch"]["imports"][0] == "from src.mod_a import helper_a, helper_c"
    assert "now declares what you asked for" in again["feedback"][0]


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


def test_a_revised_outline_that_drops_a_name_the_frozen_consumers_import_still_settles(tmp_path: Path) -> None:
    """2026-11-22, 01: the outline was revised (`helper_a` renamed), the accepted consumers still imported the old name,
    and the author of the changed module was told to follow the outline and to keep what the consumers import: no right
    answer, six attempts, PLAN_REJECTED. The changed module follows the outline; its consumers are reopened at their turn."""
    plan = _base_plan()
    renamed = {
        "src/mod_a.py": 'def helper_a_v2() -> int:\n    """Return 1."""\n    return 1\n',
        "src/mod_b.py": 'from src.mod_a import helper_a_v2\n\n\ndef helper_b() -> int:\n    """Return 2."""\n    return 2\n',
        "src/experiment.py": (
            "from src.mod_a import helper_a_v2\nfrom src.mod_b import helper_b\n\n"
            'def run_experiment() -> int:\n    """Run; writes score and time."""\n    return helper_a_v2() + helper_b()\n'
        ),
    }

    def critic(_payload: dict, n: int) -> dict | None:
        if n == 1:  # the main critic sends the outline back (a finding about the blueprint)
            return {"status": "FAIL", "issues": [{
                "blocking": True, "where": "academic_blueprint", "problem": "the success criterion is not stated", "fix": "state it",
            }]}
        return None

    def outline(_payload: dict, n: int) -> dict | None:
        if n == 1:
            return None
        revised = outline_from_plan(plan)  # the revision renames what src/mod_a.py promises
        next(m for m in revised["modules"] if m["file"] == "src/mod_a.py")["provides"] = ["helper_a_v2"]
        return revised

    def module(payload: dict, _n: int) -> dict | None:
        rel = payload["module"]["file"]
        if rel == "src/mod_a.py" and payload["module"]["provides"] == ["helper_a_v2"]:
            return _sketch(renamed[rel], needs={})
        if rel in ("src/mod_b.py", "src/experiment.py") and "helper_a_v2" in str(payload["dependencies"].get("src/mod_a.py", "")):
            return _sketch(renamed[rel], needs={})
        return None

    (_plan, interfaces, violations), _calls = _run(
        _make_orch(tmp_path), plan, {"plan_critic_guard": critic, "plan_outline": outline, "plan_module": module},
    )
    assert violations == []
    assert "helper_a_v2" in interfaces["src/mod_a.py"] and "helper_a_v2" in interfaces["src/experiment.py"]
    assert "helper_a_v2" in interfaces["src/mod_b.py"]


def _blocked_then_unparsable(counter: list[int]):
    def module(payload: dict, _n: int) -> dict | None:
        if payload["module"]["file"] != "src/mod_b.py":
            return None
        counter.append(1)
        return None if len(counter) == 1 else {"functions": [{"signature": "helper_b(", "docstring": ""}]}

    return module


def test_the_outline_hears_the_critics_objection_when_a_module_cannot_settle(tmp_path: Path) -> None:
    """§XXX P8, 02 of 2026-11-25: the critic asked for a class, the outline promised functions, the author could not satisfy
    both; the escalation told the outline only the code's last complaint, so it never learned why the author left `provides`."""
    orch = _make_orch(tmp_path)
    critic = lambda payload, _n: _critic_fail("src/mod_b.py:helper_b") if payload["module"]["file"] == "src/mod_b.py" else None  # noqa: E731
    (_, _, blockers), calls = _run(orch, _base_plan(), {"module_critic_guard": critic, "plan_module": _blocked_then_unparsable([])})
    assert blockers
    revisions = [p for a, p in calls if a == "plan_outline" and "current_outline" in p]
    assert len(revisions) == 1
    text = revisions[0]["feedback"][0]
    assert "CRITIC OBJECTION" in text and "change `provides`" in text


def test_a_critic_block_teaches_the_author_only_when_the_module_settles(tmp_path: Path) -> None:
    """§XXX P8: two blocks in two modules wrote the rule "state only in classes" into `plan_module.md`; the module that
    could not settle next to the outline's promises was one of them. A block counts once its module is accepted."""
    orch = _make_orch(tmp_path)
    critic = lambda payload, _n: _critic_fail("src/mod_b.py:helper_b") if payload["module"]["file"] == "src/mod_b.py" else None  # noqa: E731
    _run(orch, _base_plan(), {"module_critic_guard": critic, "plan_module": _blocked_then_unparsable([])})
    assert not any(e["target"] == "src/mod_b.py" for e in orch._critic_log)

    settled = _make_orch(tmp_path / "settled")
    once = lambda payload, _n: _critic_fail("src/mod_a.py:helper_a") if payload["module"]["file"] == "src/mod_a.py" else None  # noqa: E731
    _run(settled, _base_plan(), {"module_critic_guard": once})
    assert [e["target"] for e in settled._critic_log] == ["src/mod_a.py"]


def test_the_critic_prompts_keep_to_the_outlines_promises_and_the_prompt_scope() -> None:
    root = Path(__file__).resolve().parents[2] / "adk" / "agents" / "planning"
    module_critic = (root / "module_critic_guard.md").read_text(encoding="utf-8")
    outline_critic = (root / "outline_critic_guard.md").read_text(encoding="utf-8")
    assert "names in `module.provides` are fixed" in module_critic and "wrap promised functions into a class" in module_critic
    assert "never ask for a `.py` module" in outline_critic and "does not ask for" in outline_critic


def test_the_outline_prompt_has_one_complete_answer_shape_for_writing_and_revising() -> None:
    """§XXX P2, 01: three of eight revisions came back as a bare `{"revision": ...}` because the prompt showed that block
    on its own; the one example now holds the whole outline and `revision` together."""
    text = (Path(__file__).resolve().parents[2] / "adk" / "agents" / "planning" / "plan_outline.md").read_text(encoding="utf-8")
    assert text.count("## OUTPUT") == 1
    shape = text.split("## OUTPUT", 1)[1]
    assert shape.index('"modules": [') < shape.index('"academic_blueprint"') < shape.index('"revision": {')
    assert "holds only `revision` is refused" in shape and "`previous_outline`" in text


_STAR = {"modules": [
    {"file": "env.py", "depends_on": []}, {"file": "agent.py", "depends_on": []}, {"file": "baseline.py", "depends_on": []},
    {"file": "data.py", "depends_on": []}, {"file": "experiment.py", "depends_on": ["env.py", "agent.py", "baseline.py", "data.py"]},
]}


def test_the_outline_critic_is_told_by_code_which_module_is_a_hub_and_whether_its_dependencies_meet() -> None:
    """§XXXIV, 01 of 2026-11-26: an environment, an agent and a baseline that only the experiment knew left all their wiring to
    `experiment.py` (240 of 509 lines). The critic gets the counts from code; `structure_facts` does not decide anything."""
    from adk.orchestration.plan_outline import structure_facts

    facts = structure_facts(_STAR)
    assert facts["direct_dependencies"] == {"env.py": 0, "agent.py": 0, "baseline.py": 0, "data.py": 0, "experiment.py": 4}
    assert facts["possible_hubs"] == [{
        "module": "experiment.py", "depends_on": ["env.py", "agent.py", "baseline.py", "data.py"], "its_dependencies_depend_on_each_other": False,
    }]
    layered = {"modules": [
        {"file": "env.py", "depends_on": []}, {"file": "agent.py", "depends_on": []}, {"file": "baseline.py", "depends_on": ["env.py"]},
        {"file": "trainer.py", "depends_on": ["env.py", "agent.py"]}, {"file": "experiment.py", "depends_on": ["trainer.py", "baseline.py"]},
    ]}
    assert structure_facts(layered)["possible_hubs"] == []  # nothing has four dependencies
    meeting = {"modules": [*_STAR["modules"][:4], {"file": "experiment.py", "depends_on": ["env.py", "agent.py", "baseline.py", "data.py"]}]}
    meeting["modules"][1] = {"file": "agent.py", "depends_on": ["env.py"]}  # the agent uses the environment: they meet elsewhere
    assert structure_facts(meeting)["possible_hubs"][0]["its_dependencies_depend_on_each_other"] is True


def test_the_outline_critic_receives_the_structure_of_the_outline_it_reviews(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    _result, calls = _run(orch, _base_plan(), {})
    reviews = [p for a, p in calls if a == "outline_critic_guard"]
    assert reviews and all(set(p["structure"]) == {"direct_dependencies", "possible_hubs"} for p in reviews)
    assert reviews[0]["structure"]["direct_dependencies"].keys() == {m["file"] for m in reviews[0]["outline"]["modules"]}


def test_the_prompts_ask_for_modularity_gently() -> None:
    root = Path(__file__).resolve().parents[2] / "adk" / "agents" / "planning"
    critic = (root / "outline_critic_guard.md").read_text(encoding="utf-8")
    assert "`structure`" in critic and "`possible_hubs`" in critic and "Modularity, gently" in critic
    assert "Raise it once" in critic and "do not raise it again" in critic and "one-time modularity suggestion of point 5" in critic
    author = (root / "plan_outline.md").read_text(encoding="utf-8")
    assert "Prefer a layered, modular design" in author and "This is a preference, not a rule" in author and "never a module for its own sake" in author
