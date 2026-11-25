"""Redesign: when the queue ended with failed modules the designer revises the design from an audit of what is really implemented, instead of the re-plan that touches only the failed."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from adk.hypergraph import load
from adk.mocks.staged import sketch_of, staged_answer
from adk.orchestration.common import _RunState
from adk.orchestration.implementation_audit import (
    audit_facts,
    compact_audit,
    source_facts,
)
from adk.orchestration.redesign_rules import decisions_of, revision_violations
from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.staged_planning import _MOD_A, _MOD_B, _base_plan, _make_orch, _run

_FIGURES = 'def plots() -> None:\n    """Figures."""\n    return None\n'


_HELPER_C = 'def helper_c() -> int:\n    """Return 3."""\n    ...\n'


_MOD_B_SPLIT = (
    "from src.mod_a import helper_a\nfrom src.mod_c import helper_c\n\n\n"
    'def helper_b() -> int:\n    """Return what the two helpers give."""\n    ...\n'
)


_TEST = "from src import {name}\n\n\ndef test_it() -> None:\n    assert {name}.{fn}() == {value}\n"


def _project(tmp_path: Path) -> tuple[NeuroSymbolicOrchestrator, dict[str, Any], _RunState]:
    """A built project: four modules and two tests that passed, `src/mod_b.py` failed after every repair, the
    experiment waiting for it. The outline and the blueprint are saved as planning saves them."""
    orch = _make_orch(tmp_path)
    (plan_out, interfaces, blockers), _calls = _run(orch, _base_plan())
    assert blockers == []
    sources = {
        "src/mod_a.py": _MOD_A, "src/mod_b.py": _MOD_B, "src/figures.py": _FIGURES,
        "src/experiment.py": 'from src.mod_a import helper_a\nfrom src.mod_b import helper_b\n\n\ndef run_experiment() -> int:\n    """Run; writes score."""\n    return helper_a() + helper_b()\n',
        "tests/test_mod_a.py": _TEST.format(name="mod_a", fn="helper_a", value=1),
        "tests/test_mod_b.py": _TEST.format(name="mod_b", fn="helper_b", value=2),
    }
    for rel, source in sources.items():
        (orch.workspace_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (orch.workspace_dir / rel).write_text(source, encoding="utf-8")
    blueprint = {**plan_out["academic_blueprint"], "interfaces": interfaces, "thesis_type": "inzynierska", "template_name": "thesis_plodz"}
    orch.blueprint_path.write_text(json.dumps(blueprint), encoding="utf-8")
    orch.plan_outline_path.write_text(json.dumps(plan_out["outline"]), encoding="utf-8")
    h = orch._build_project_hypergraph(interfaces, blueprint, plan_out["tasks"])
    orch.hypergraph = h
    for vertex in h.vertices.values():
        if vertex.kind in ("code", "entry", "test"):
            vertex.state = "verified"
    h.vertices["src/mod_b.py"].state, h.vertices["src/mod_b.py"].failures, h.vertices["src/mod_b.py"].attempts = "failed", 3, 8
    h.vertices["src/mod_b.py"].history.append({"task_id": "T4", "issues": ["Pytest failure: FAILED tests/test_mod_b.py::test_it - AssertionError"]})
    h.vertices["src/experiment.py"].state = "impl"
    queue = [
        {"task_id": "T1", "target_node": "src/mod_a.py", "assigned_agent": "seed_coder", "status": "DONE"},
        {"task_id": "T2", "target_node": "src/mod_b.py", "assigned_agent": "seed_coder", "status": "FAILED"},
        {"task_id": "T3", "target_node": "src/experiment.py", "assigned_agent": "seed_coder", "status": "WAITING"},
    ]
    orch.task_queue_path.write_text(json.dumps(queue), encoding="utf-8")
    return orch, plan_out, _RunState(user_prompt="p", max_retries=5, multi_cycle_waves=True, tasks=queue)


def _split_outline(current: dict[str, Any]) -> dict[str, Any]:
    """The designer's answer: `src/mod_b.py` is cut in two, with a new helper module under it."""
    outline = copy.deepcopy(current)
    mod_b = next(m for m in outline["modules"] if m["file"] == "src/mod_b.py")
    mod_b["depends_on"] = ["src/mod_a.py", "src/mod_c.py"]
    outline["modules"].insert(1, {"file": "src/mod_c.py", "purpose": "Helper of the second half.", "depends_on": ["src/mod_a.py"], "provides": ["helper_c() -> int"]})
    keep = {m["file"]: {"status": "keep", "why": "it works"} for m in outline["modules"]}
    keep["src/mod_b.py"] = {"status": "change", "why": "does two things; the second half moves to a helper"}
    keep["src/mod_c.py"] = {"status": "new", "why": "the second half of mod_b"}
    return {**outline, "revision": {"modules": keep, "diagnosis": {"src/mod_b.py": {"cause": "split", "why": "two jobs in one file"}}}}


def _agents(orch: NeuroSymbolicOrchestrator, plan_out: dict[str, Any], designer: Callable[[dict, int], dict]) -> list[tuple[str, dict, dict]]:
    """The agents of a redesign: the auditor describes, the designer answers `designer(payload, n)`, the module authors
    declare, the critics pass. Returns the calls (agent, payload, keyword arguments)."""
    calls: list[tuple[str, dict, dict]] = []
    sketches = {"src/mod_c.py": sketch_of(_HELPER_C), "src/mod_b.py": sketch_of(_MOD_B_SPLIT)}

    def fake(md: Any, payload: dict, **kw: Any) -> dict:
        agent = Path(md).stem
        calls.append((agent, payload, kw))
        n = sum(1 for a, _p, _k in calls if a == agent)
        if agent == "implementation_auditor":
            functions = {f["name"]: "Returns a number." for f in payload["card"]["functions"]}
            return {"status": "ok", "output": {"functions": functions, "matches_interface": True, "suspicious": []}}
        if agent == "plan_outline":
            return {"status": "ok", "output": designer(payload, n)}
        if agent == "plan_module" and payload["module"]["file"] in sketches:
            return {"status": "ok", "output": {**sketches[payload["module"]["file"]], "needs": {}}}
        return {"status": "ok", "output": staged_answer(plan_out["_plan"], agent, payload)}

    orch._call_agent = fake
    return calls


def _redesign(tmp_path: Path, designer: Callable[[dict, int], dict] | None = None) -> tuple[NeuroSymbolicOrchestrator, _RunState, Any, list[tuple[str, dict, dict]]]:
    orch, plan_out, state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    calls = _agents(orch, plan_out, designer or (lambda payload, _n: _split_outline(payload["current_outline"])))
    return orch, state, orch._redesign_failed(state, ["src/mod_b.py"]), calls


def _events(orch: NeuroSymbolicOrchestrator, kind: str) -> list[dict]:
    lines = orch.logger.events_path.read_text(encoding="utf-8").splitlines()
    return [e for e in map(json.loads, lines) if e["event"] == kind]


def test_the_facts_of_a_file_are_counted_from_its_code() -> None:
    source = (
        "import os\n\nN: int = 3\n\n\nclass A:\n    x: int = 1\n\n    def go(self, k: int) -> int:\n        \"\"\"Go far.\"\"\"\n"
        "        if k < 0:\n            raise ValueError(k)\n        return os.getpid() + helper(k)\n\n\ndef helper(k: int) -> int:\n    return k\n"
    )
    facts = source_facts(source)
    assert facts["constants"] == ["N"] and facts["classes"] == [{"name": "A", "bases": [], "attributes": ["x: int = 1"]}]
    go = next(f for f in facts["functions"] if f["name"] == "A.go")
    assert go["calls"] == ["ValueError", "helper", "os.getpid"] and go["raises"] == ["ValueError"] and go["docstring"] == "Go far."
    assert source_facts("def f(:") == {"parses": False}


def test_the_audit_knows_each_module_its_neighbours_its_tests_and_what_the_plan_declares_and_the_file_lacks(tmp_path: Path) -> None:
    orch, _plan, _state = _project(tmp_path)
    (orch.workspace_dir / "src/mod_b.py").write_text("def other() -> int:\n    return 2\n", encoding="utf-8")  # helper_b is gone
    interfaces = json.loads(orch.blueprint_path.read_text(encoding="utf-8"))["interfaces"]
    cards = audit_facts(orch._project_h(), orch.workspace_dir, interfaces)
    assert set(cards) == {"src/mod_a.py", "src/mod_b.py", "src/experiment.py", "src/figures.py"}
    assert cards["src/mod_b.py"]["lacks_planned"] == ["helper_b"] and cards["src/mod_a.py"]["lacks_planned"] == []
    assert cards["src/mod_a.py"]["used_by"] == ["src/experiment.py", "src/mod_b.py"] and cards["src/experiment.py"]["uses"].keys() == {"src/mod_a.py", "src/mod_b.py"}
    assert cards["src/mod_b.py"]["state"] == "failed" and cards["src/mod_b.py"]["errors"] and cards["src/mod_a.py"]["tests"] == [{"file": "tests/test_mod_a.py", "state": "verified"}]


def test_a_file_is_described_once_and_again_only_when_it_changes(tmp_path: Path) -> None:
    orch, plan_out, _state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    calls = _agents(orch, plan_out, lambda payload, _n: payload)
    first = orch._implementation_audit(["src/mod_b.py"])
    assert [p["file"] for a, p, _k in calls if a == "implementation_auditor"] and all(k["model_tier"] == "SML" for a, _p, k in calls)
    described = len(calls)
    assert described == 4 and first["files"]["src/mod_a.py"]["behavior"]["functions"] == {"helper_a": "Returns a number."}
    orch._implementation_audit([])
    assert len(calls) == described  # nothing changed: the descriptions are kept by the fingerprint of each file
    (orch.workspace_dir / "src/mod_a.py").write_text(_MOD_A.replace("return 1", "return 5"), encoding="utf-8")
    orch._implementation_audit([])
    assert [p["file"] for a, p, _k in calls[described:] if a == "implementation_auditor"] == ["src/mod_a.py"]


def test_what_the_designer_reads_has_no_body_and_shrinks_what_passed_quietly(tmp_path: Path) -> None:
    orch, plan_out, _state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    _agents(orch, plan_out, lambda payload, _n: payload)
    view = compact_audit(orch._implementation_audit(["src/mod_b.py"]))
    assert "return" not in json.dumps(view) and view["src/mod_b.py"]["errors"] and view["src/mod_a.py"]["does"] == {"helper_a": "Returns a number."}
    small = compact_audit(orch._implementation_audit(["src/mod_b.py"]), budget=200)
    assert "does" not in small["src/mod_a.py"] and "declares" not in small["src/mod_a.py"] and small["src/mod_b.py"]["errors"] and small["src/mod_b.py"]["does"]


def test_the_statuses_and_the_outline_must_say_the_same(tmp_path: Path) -> None:
    _orch, plan_out, _state = _project(tmp_path)
    from adk.orchestration.plan_outline import outline_of

    old = outline_of(plan_out["outline"])
    answer = _split_outline(plan_out["outline"])
    new, decisions = outline_of(answer), decisions_of(answer)
    assert revision_violations(old, new, decisions, set()) == []
    wrong = {**decisions, "src/mod_a.py": {"status": "keep", "why": ""}, "src/mod_b.py": {"status": "keep", "why": ""}}
    assert any("src/mod_b.py" in v and "differs" in v for v in revision_violations(old, new, wrong, set()))
    assert any("src/mod_c.py" in v and "no status" in v for v in revision_violations(old, new, {k: v for k, v in decisions.items() if k != "src/mod_c.py"}, set()))
    assert any("src/mod_c.py" in v and "already has a file" in v for v in revision_violations(old, new, decisions, {"src/mod_c.py"}))
    assert any("not one of" in v for v in revision_violations(old, new, {**decisions, "src/mod_b.py": {"status": "rewrite", "why": ""}}, set()))
    unchanged = {rel: {"status": "keep", "why": ""} for rel in decisions if rel != "src/mod_c.py"}
    assert any("every module is `keep`" in v for v in revision_violations(old, old, unchanged, set()))


def test_a_redesign_splits_a_module_keeps_what_works_and_asks_for_what_is_not_verified(tmp_path: Path) -> None:
    orch, state, result, calls = _redesign(tmp_path)
    assert result is not None and orch.__dict__["_redesigns"] == 1
    applied = _events(orch, "REDESIGN_APPLIED")[-1]
    assert applied["redesigned"] == ["src/mod_b.py", "src/mod_c.py"] and "src/mod_a.py" in applied["kept"]
    h = load(orch.hypergraph_path)
    assert h.vertices["src/mod_a.py"].state == "verified" and h.vertices["tests/test_mod_a.py"].state == "verified"  # nothing of it is done again
    assert h.vertices["src/mod_b.py"].state == "impl" and h.vertices["src/mod_b.py"].failures == 0  # the old code stays as the base
    assert "src/mod_c.py" in h.vertices and "return 2" in (orch.workspace_dir / "src/mod_b.py").read_text(encoding="utf-8")  # the old code of mod_b is the base
    assert "NotImplementedError" in (orch.workspace_dir / "src/mod_c.py").read_text(encoding="utf-8")  # the stub of a new module
    targets = [t["target_node"] for t in result["tasks"]]
    assert "src/mod_c.py" in targets and "src/mod_b.py" in targets and "tests/test_mod_c.py" in targets
    assert "src/mod_a.py" not in targets and "tests/test_mod_a.py" not in targets
    assert [t["task_id"] for t in result["tasks"]] == [f"D1_{i}" for i in range(1, len(targets) + 1)]
    assert {t["task_id"] for t in state.tasks if t["status"] in ("DONE", "FAILED")} == {"T1", "T2"}  # the record stays, the waiting goes
    blueprint = json.loads(orch.blueprint_path.read_text(encoding="utf-8"))
    assert "src/mod_c.py" in blueprint["interfaces"] and "src/mod_c.py" in [m["file"] for m in json.loads(orch.plan_outline_path.read_text(encoding="utf-8"))["modules"]]
    assert [k["model_tier"] for a, _p, k in calls if a == "plan_outline"] == ["LRM"] and [k["model_tier"] for a, _p, k in calls if a == "implementation_auditor"] == ["SML"] * 4


def test_the_designer_gets_the_audit_the_plan_and_the_errors_and_no_body(tmp_path: Path) -> None:
    _orch, _state, _result, calls = _redesign(tmp_path)
    payload = next(p for a, p, _k in calls if a == "plan_outline")
    assert set(payload["revision"]) == {"reason", "failed", "implementation", "unresolved_errors"} and payload["current_outline"]["entrypoint"]
    assert payload["revision"]["unresolved_errors"]["src/mod_b.py"][0].startswith("Pytest failure")
    assert "return 1" not in json.dumps(payload) and payload["revision"]["implementation"]["src/mod_a.py"]["declares"] == ["helper_a() -> int"]
    modules = [p["module"]["file"] for a, p, _k in calls if a == "plan_module"]
    assert sorted(modules) == ["src/mod_b.py", "src/mod_c.py"]  # the others stay accepted
    for agent, folder in (("plan_outline", "planning"), ("implementation_auditor", "verification")):
        sent = {k for a, p, _k in calls if a == agent for k in p} | (set(payload["revision"]) if agent == "plan_outline" else set())
        prompt = Path(f"adk/agents/{folder}/{agent}.md").read_text(encoding="utf-8")
        assert [k for k in sorted(sent) if f"`{k}`" not in prompt] == [], agent


def test_the_tests_of_what_uses_a_redesigned_module_are_verified_again(tmp_path: Path) -> None:
    def change_mod_a(payload: dict, _n: int) -> dict:
        current = payload["current_outline"]
        statuses = {m["file"]: {"status": "keep", "why": ""} for m in current["modules"]}
        statuses["src/mod_a.py"] = {"status": "change", "why": "the base of both"}
        return {**current, "revision": {"modules": statuses}}

    orch, _state, result, _calls = _redesign(tmp_path, change_mod_a)
    h = load(orch.hypergraph_path)
    assert result is not None and h.vertices["tests/test_mod_b.py"].state == "stale" and h.vertices["tests/test_mod_a.py"].state == "spec"
    assert h.vertices["src/mod_b.py"].state == "failed" and h.vertices["src/mod_b.py"].attempts == 0  # it starts again, its failures stay
    assert h.vertices["src/mod_b.py"].failures == 3


def test_a_module_that_goes_leaves_with_its_tests(tmp_path: Path) -> None:
    def drop_mod_b(payload: dict, _n: int) -> dict:
        outline = copy.deepcopy(payload["current_outline"])
        outline["modules"] = [m for m in outline["modules"] if m["file"] != "src/mod_b.py"]
        for module in outline["modules"]:
            module["depends_on"] = [d for d in module["depends_on"] if d != "src/mod_b.py"]
        statuses = {m["file"]: {"status": "keep", "why": ""} for m in outline["modules"]}
        statuses["src/experiment.py"] = {"status": "change", "why": "does not need mod_b"}
        statuses["src/mod_b.py"] = {"status": "remove", "why": "its job is the experiment's"}
        return {**outline, "revision": {"modules": statuses}}

    plan = _base_plan()
    plan["interfaces"]["src/experiment.py"] = 'from src.mod_a import helper_a\n\n\ndef run_experiment() -> int:\n    """Run; writes score and time."""\n    return helper_a()\n'
    orch, plan_out, state = _project(tmp_path)
    plan_out["_plan"] = plan
    _agents(orch, plan_out, drop_mod_b)
    result = orch._redesign_failed(state, ["src/mod_b.py"])
    assert result is not None
    assert not (orch.workspace_dir / "src/mod_b.py").exists() and not (orch.workspace_dir / "tests/test_mod_b.py").exists()
    assert "src/mod_b.py" not in load(orch.hypergraph_path).vertices and _events(orch, "REDESIGN_REMOVED")[-1]["module"] == "src/mod_b.py"


def test_a_run_planned_before_the_outline_was_saved_is_re_planned_as_before(tmp_path: Path) -> None:
    orch, plan_out, state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    calls = _agents(orch, plan_out, lambda payload, _n: payload)
    orch.plan_outline_path.unlink()
    assert orch._redesign_failed(state, ["src/mod_b.py"]) is None and calls == []
    assert _events(orch, "REDESIGN_FALLBACK")[-1]["reason"] == "the outline of the plan is not saved"


def test_a_redesign_that_changes_nothing_hands_the_round_to_the_re_plan(tmp_path: Path) -> None:
    def all_keep(payload: dict, _n: int) -> dict:
        current = payload["current_outline"]
        return {**current, "revision": {"modules": {m["file"]: {"status": "keep", "why": "fine"} for m in current["modules"]}}}

    orch, state, result, calls = _redesign(tmp_path, all_keep)
    assert result is None and "_redesigns" not in orch.__dict__
    assert [a for a, _p, _k in calls].count("plan_outline") == 2  # the first answer and one correction
    assert "every module is `keep`" in next(p for a, p, _k in calls[::-1] if a == "plan_outline")["feedback"][0]
    assert orch._project_h().vertices["src/mod_b.py"].state == "failed" and state.tasks[-1]["task_id"] == "T3"  # nothing was touched


def test_a_wrong_answer_is_corrected_once(tmp_path: Path) -> None:
    def first_wrong(payload: dict, n: int) -> dict:
        answer = _split_outline(payload["current_outline"])
        if n == 1:
            answer["revision"]["modules"].pop("src/mod_c.py")
        else:
            assert any("no status" in f for f in payload["feedback"])
        return answer

    _orch, _state, result, calls = _redesign(tmp_path, first_wrong)
    assert result is not None and [a for a, _p, _k in calls].count("plan_outline") == 2


def test_the_rounds_of_redesign_are_limited_and_can_be_switched_off(tmp_path: Path) -> None:
    orch, plan_out, state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    calls = _agents(orch, plan_out, lambda payload, _n: _split_outline(payload["current_outline"]))
    orch.max_redesigns = 0
    assert orch._redesign_failed(state, ["src/mod_b.py"]) is None and calls == []
    orch.max_redesigns, orch.__dict__["_redesigns"] = 1, 1
    assert orch._redesign_failed(state, ["src/mod_b.py"]) is None and calls == []


def test_a_redesign_round_counts_against_no_limit_of_the_re_plan(tmp_path: Path) -> None:
    orch, plan_out, state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    calls = _agents(orch, plan_out, lambda payload, _n: _split_outline(payload["current_outline"]))
    replanned = orch._replan_failed(state)
    assert replanned is not None and replanned["tasks"][0]["task_id"] == "D1_1" and "task_planner" not in [a for a, _p, _k in calls]
    assert "_replan_progress" not in orch.__dict__  # the limits of the re-plan (6 rounds, 3 without progress) did not see it


def test_when_the_rounds_of_redesign_are_spent_the_re_plan_of_the_failed_takes_the_round(tmp_path: Path) -> None:
    orch, plan_out, state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    calls = _agents(orch, plan_out, lambda payload, _n: _split_outline(payload["current_outline"]))
    orch.max_redesigns = 0
    orch._replan_failed(state)
    assert [a for a, _p, _k in calls] == ["task_planner"] and len(orch.__dict__["_replan_progress"]) == 1


def test_a_designer_that_never_gives_usable_guidelines_is_asked_a_limited_number_of_times(tmp_path: Path) -> None:
    def all_keep(payload: dict, _n: int) -> dict:
        current = payload["current_outline"]
        return {**current, "revision": {"modules": {m["file"]: {"status": "keep", "why": "fine"} for m in current["modules"]}}}

    orch, plan_out, state = _project(tmp_path)
    plan_out["_plan"] = _base_plan()
    calls = _agents(orch, plan_out, all_keep)
    assert [orch._redesign_failed(state, ["src/mod_b.py"]) for _ in range(6)] == [None] * 6
    assert [a for a, _p, _k in calls].count("plan_outline") == 2 * 4  # two answers in each of the four attempts, then no more
    assert len(_events(orch, "REDESIGN_STARTED")) >= 4


# --- the designer reads code when the descriptions are not enough ------------------------------------------------


def _asks_for(*paths: str) -> dict:
    return {"revision": {"need_source": list(paths)}}


def test_the_designer_may_ask_to_read_the_code_of_a_file_and_the_request_costs_no_answer(tmp_path: Path) -> None:
    def designer(payload: dict, n: int) -> dict:
        if n == 1:
            assert "sources" not in payload["revision"]
            return _asks_for("src/mod_b.py", "src/ghost.py", "tests/test_mod_b.py", "src/mod_b.py")  # only a module that is implemented may be read, each once
        assert list(payload["revision"]["sources"]) == ["src/mod_b.py"] and "return 2" in payload["revision"]["sources"]["src/mod_b.py"]
        assert "feedback" not in payload  # the request was not a wrong answer
        return _split_outline(payload["current_outline"])

    orch, _state, result, calls = _redesign(tmp_path, designer)
    assert result is not None and [a for a, _p, _k in calls].count("plan_outline") == 2
    assert _events(orch, "REDESIGN_SOURCE_GRANTED")[-1]["files"] == ["src/mod_b.py"]
    assert [e["attempt"] for e in _events(orch, "REDESIGN_GUIDELINES")][-1:] == [1]  # one answer was used, the correction is still there
    prompt = Path("adk/agents/planning/plan_outline.md").read_text(encoding="utf-8")
    assert "`sources`" in prompt and "need_source" in prompt


def test_a_second_request_for_code_is_not_answered(tmp_path: Path) -> None:
    def designer(payload: dict, n: int) -> dict:
        if n <= 2:
            return _asks_for("src/mod_b.py")
        return _split_outline(payload["current_outline"])

    orch, _state, result, calls = _redesign(tmp_path, designer)
    assert result is not None and [a for a, _p, _k in calls].count("plan_outline") == 3  # request, request again (a wrong answer), the answer
    assert len(_events(orch, "REDESIGN_SOURCE_GRANTED")) >= 1
    last = [p for a, p, _k in calls if a == "plan_outline"][-1]
    assert "feedback" in last  # the second request was told what is wrong with it, like any answer without an outline


def test_a_request_for_nothing_the_designer_may_read_is_an_answer(tmp_path: Path) -> None:
    def designer(payload: dict, n: int) -> dict:
        return _asks_for("src/ghost.py", "tests/test_mod_a.py") if n == 1 else _split_outline(payload["current_outline"])

    orch, _state, result, calls = _redesign(tmp_path, designer)
    assert result is not None and [a for a, _p, _k in calls].count("plan_outline") == 2
    assert not [e for e in _events(orch, "REDESIGN_SOURCE_GRANTED") if e["files"] == ["src/ghost.py"]]
