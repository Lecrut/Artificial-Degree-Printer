"""Audit VII (2026-11-18): a plan that cannot work is rejected before any code, by code first and then by the critic.

The cases are the plans of 2026-11-17: impossible doctests and an entrypoint that ignores the planned modules (01),
an attribute declared by `self.x = ...` that vanished from the stub and crashed the run (02)."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph import build_from_plan, code_violations, diff, observe
from adk.tools.verification.contract_check import stub_source
from tests.test_audit_vi import _ENTRY, _GOOD, _rules

_AGENT = (
    '"""Agent."""\nfrom src.config import CHANNELS\n\n\n'
    "class QAgent:\n"
    '    """Q-learning agent."""\n\n'
    "    def __init__(self, lr: float) -> None:\n"
    '        """Store the learning rate."""\n        self.lr = lr\n\n'
    "    def learn(self, state: tuple, next_state: tuple) -> None:\n"
    '        """Update the table.\n\n'
    "        >>> agent = QAgent(lr=0.1)\n"
    "        >>> ns = (0,)*9; ns[0]=1\n"
    "        >>> agent.learn((0,)*9, ns)\n"
    '        """\n\n'
    "    def reset(self) -> tuple:\n"
    '        """Empty board.\n\n'
    "        >>> agent = QAgent(lr=0.1)\n"
    "        >>> agent.reset()\n"
    "        >>> next_s = agent.reset()\n"
    "        >>> next_s[4] == 0\n"
    "        True\n"
    '        """\n'
)
_EXPERIMENT_USING_AGENT = _GOOD["src/experiment.py"].replace(
    "from src.data_generator import generate_sample\n",
    "from src.data_generator import generate_sample\nfrom src.agent import QAgent\n",
)


def _plan(**changes: str) -> dict[str, str]:
    return {**_GOOD, "src/agent.py": _AGENT, "src/experiment.py": _EXPERIMENT_USING_AGENT, **changes}


def test_doctests_that_no_implementation_can_satisfy_are_rejected():
    """01: `ns[0]=1` on a tuple (TypeError for every implementation) and a bare `reset()` whose value doctest prints.
    Examples that only read the result of a stub (`agent.learn`, `next_s[4]`) are not judged."""
    found = [v for v in code_violations(_plan(), _ENTRY)[1]]
    invalid = [v for v in found if v.rule == "DOCTEST_INVALID_ON_STUBS"]
    assert len(invalid) == 1 and "ns[0]=1" in invalid[0].detail and "TypeError" in invalid[0].detail
    discards = [v for v in found if v.rule == "DOCTEST_DISCARDS_RETURN"]
    assert len(discards) == 1 and "agent.reset()" in discards[0].detail and discards[0].culprit == "src/agent.py"


def test_correct_doctests_pass():
    fixed = _AGENT.replace("ns = (0,)*9; ns[0]=1", "ns = (1,) + (0,)*8").replace(
        ">>> agent.reset()\n", ">>> _ = agent.reset()\n"
    )
    assert code_violations(_plan(**{"src/agent.py": fixed}), _ENTRY)[1] == []


def test_entrypoint_that_never_imports_a_planned_module_is_rejected():
    """01: run_experiment in config.py imported nothing; the coder rewrote the game inside it (83x DATA_FAILED)."""
    plan = {**_GOOD, "src/agent.py": _AGENT.replace(">>> agent.reset()\n", ">>> _ = agent.reset()\n").replace(
        "ns = (0,)*9; ns[0]=1", "ns = (1,) + (0,)*8")}
    found = [v for v in code_violations(plan, _ENTRY)[1] if v.rule == "ENTRYPOINT_DOES_NOT_USE"]
    assert len(found) == 1 and "src/agent.py" in found[0].detail and found[0].culprit == "src/experiment.py"


def test_plot_module_is_not_required_to_be_imported_by_the_experiment():
    plots = '"""Plots."""\n\n\ndef generate_plots(output_dir: str) -> None:\n    """Write the figures."""\n'
    assert "ENTRYPOINT_DOES_NOT_USE" not in _rules(code_violations({**_GOOD, "plot_results.py": plots}, _ENTRY)[1])


def test_stub_keeps_attributes_declared_by_self_assignment(tmp_path: Path):
    """02: `self.threshold = threshold` vanished with the body of __init__; the spec gate rejected the harness's own
    stubs and the run crashed before its first task."""
    baseline = (
        '"""Baseline."""\n\n\nclass ZScoreBaseline:\n    """Detector."""\n\n'
        "    def __init__(self, threshold: float = 3.0) -> None:\n"
        '        """Store the threshold."""\n        self.threshold: float = threshold\n        self.fitted = False\n\n'
        "    def detect(self, x: list) -> list:\n        \"\"\"Flags.\"\"\"\n        pass\n"
    )
    stub = stub_source(baseline)
    assert "threshold: 'float'" in stub and "fitted: 'object'" in stub and "raise NotImplementedError" in stub
    interfaces = {**_GOOD, "src/baseline.py": baseline}
    experiment = _GOOD["src/experiment.py"].replace(
        "from src.data_generator import generate_sample\n",
        "from src.data_generator import generate_sample\nfrom src.baseline import ZScoreBaseline\n",
    )
    interfaces["src/experiment.py"] = experiment
    h, problems = build_from_plan(interfaces, _ENTRY, [], [], [])
    assert problems == []
    for rel, src in interfaces.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(stub_source(src), encoding="utf-8")
    assert diff(h, observe(tmp_path)) == []


# --- chapters come from the plan (Audit VIII C2) ------------------------------------------------------------------


def test_a_section_task_maps_to_its_chapter():
    """01: T1 "draft Section 1.1 (Introduction)" matched no chapter; ch1 stayed `spec` although T1 was DONE."""
    from adk.hypergraph.schedule import vertex_of

    chapters = [{"index": 1, "title": "Wstęp", "focus": "cel"}, {"index": 5, "title": "Wnioski", "focus": "wnioski"}]
    h, _ = build_from_plan(_GOOD, _ENTRY, [], chapters, [])
    assert vertex_of(h, "thesis.md", "Draft Section 1.1 (Introduction)") == "thesis.md#ch1"
    assert vertex_of(h, "thesis.md", "Write Rozdział 5") == "thesis.md#ch5"


def test_the_thesis_is_complete_with_the_planned_chapters():
    """01: five planned chapters, the final gate demanded a sixth and Q1_CH6 wrote a chapter outside the plan."""
    from adk.orchestration.factual_audit import thesis_missing_chapters

    thesis = "\n".join(f"## Rozdział {n}: T\n\ntext" for n in range(1, 6))
    assert thesis_missing_chapters(thesis, [1, 2, 3, 4, 5]) == []
    assert thesis_missing_chapters(thesis) == [6]  # the canonical six only without a planned outline


def test_expected_chapters_follow_the_blueprint(tmp_path: Path):
    import json

    from tests.test_root_causes_1115 import _orch

    orch = _orch(tmp_path)
    assert orch._expected_chapters() == [1, 2, 3, 4, 5, 6]
    orch.blueprint_path.write_text(json.dumps({"planned_chapters": [{"index": i, "title": "t"} for i in range(1, 6)]}), encoding="utf-8")
    assert orch._expected_chapters() == [1, 2, 3, 4, 5]


# --- the plan critic ----------------------------------------------------------------------------------------------


def _critic_orch(tmp_path: Path, verdicts: list[dict], plans: list[dict]):
    from tests.test_root_causes_1115 import _orch

    orch = _orch(tmp_path)
    calls = {"critic": [], "planner": []}

    def agents(md, payload, **_kw):
        if Path(md).name == "plan_critic_guard.md":
            calls["critic"].append(payload)
            return {"status": "ok", "output": verdicts[min(len(calls["critic"]), len(verdicts)) - 1]}
        calls["planner"].append(payload)
        return {"status": "ok", "output": plans[min(len(calls["planner"]), len(plans)) - 1]}

    orch._call_agent = agents
    return orch, calls


_PLAN = {"tasks": [{"task_id": "T1", "target_node": "src/experiment.py", "description": "x"}], "interfaces": _GOOD, "entrypoint": _ENTRY}
_BLOCK = {"status": "FAIL", "issues": [{"blocking": True, "where": "src/experiment.py", "problem": "never runs the baseline", "fix": "call it"}]}
_ADVICE = {"status": "PASS", "issues": [{"blocking": False, "where": "T1", "problem": "vague", "fix": "be precise"}]}


_CRITIC_FIX = {"academic_blueprint": {"baseline_comparison": "run_experiment runs the baseline and the method"}}


def test_blocking_critic_finding_goes_back_to_the_planner(tmp_path: Path):
    orch, calls = _critic_orch(tmp_path, [_BLOCK, {"status": "PASS", "issues": []}], [_CRITIC_FIX])
    plan, _, violations = orch._validated_plan(_PLAN, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert violations == [] and len(calls["planner"]) == 1 and len(calls["critic"]) == 2
    assert "PLAN_CRITIC [src/experiment.py]: never runs the baseline Fix: call it" in calls["planner"][0]["error_feedback"]


def test_plan_still_blocked_by_the_critic_after_two_corrections_is_rejected(tmp_path: Path):
    """No more rewriting a FAIL into PASS: the critic's blocking verdict stops the run."""
    orch, calls = _critic_orch(tmp_path, [_BLOCK], [_CRITIC_FIX])
    _, _, violations = orch._validated_plan(_PLAN, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert len(calls["planner"]) == 2 and any("never runs the baseline" in v for v in violations)
    assert orch._plan_rejected(violations, _PLAN["tasks"])["stop"]["status"] == "PLAN_REJECTED"


def test_advice_alone_neither_retries_nor_blocks(tmp_path: Path):
    orch, calls = _critic_orch(tmp_path, [_ADVICE], [_PLAN])
    _, _, violations = orch._validated_plan(_PLAN, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert violations == [] and calls["planner"] == []


def test_critic_is_not_asked_about_a_plan_the_code_rejects(tmp_path: Path):
    broken = {**_PLAN, "interfaces": {**_GOOD, "src/experiment.py": _GOOD["src/experiment.py"].replace("run_experiment()", "run_experiment(x)")}}
    orch, calls = _critic_orch(tmp_path, [{"status": "PASS", "issues": []}], [broken])
    _, _, violations = orch._validated_plan(broken, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert calls["critic"] == [] and any("ENTRYPOINT_HAS_ARGUMENTS" in v for v in violations)


def test_unreadable_critic_answer_blocks_nothing_and_is_logged(tmp_path: Path):
    orch, calls = _critic_orch(tmp_path, [{"answer": "looks fine"}], [_PLAN])
    _, _, violations = orch._validated_plan(_PLAN, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert violations == [] and calls["planner"] == []



# --- correcting a plan: a patch of the plan the planner sees, kept only when it makes progress (2026-11-18) ------

_BAD_DOCTEST = _GOOD["src/data_generator.py"].replace(
    '"""One sample."""', '"""One sample.\n\n    >>> v = (1, 2); v[0] = 0\n    """'
)


def _patched(orch, run) -> list[dict]:
    """PLAN_PATCHED events written while `run()` ran (the event log is shared by the test session)."""
    import json

    path = orch.logger.events_path
    seen = len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0
    result = run()
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()[seen:]]
    return result, [e for e in events if e["event"] == "PLAN_PATCHED"]


def test_a_correction_patches_only_what_is_wrong(tmp_path: Path):
    broken = {**_PLAN, "interfaces": {**_GOOD, "src/data_generator.py": _BAD_DOCTEST}}
    patch = {"interfaces": {"src/data_generator.py": _GOOD["src/data_generator.py"]}}
    orch, calls = _critic_orch(tmp_path, [{"status": "PASS", "issues": []}], [patch])
    (plan, interfaces, violations), patched = _patched(orch, lambda: orch._validated_plan(broken, {"user_prompt": "p"}, tmp_path / "planner.md"))
    assert violations == [] and interfaces == _GOOD and plan["tasks"] == _PLAN["tasks"]
    sent = calls["planner"][0]
    assert sent["current_plan"]["interfaces"]["src/data_generator.py"] == _BAD_DOCTEST
    assert "do not write a new plan" in sent["error_feedback"]
    assert len(patched) == 1 and patched[0]["accepted"] is True and patched[0]["changed"] == ["src/data_generator.py"] and patched[0]["new"] == []


def test_a_rewrite_keeps_only_the_parts_that_do_not_break_the_plan(tmp_path: Path):
    """The 2026-11-18 run: each correction was a different plan with different mistakes. Of a patch that fixes one
    module and breaks another, the fix is kept and the breaking change is rejected and reported."""
    broken = {**_PLAN, "interfaces": {**_GOOD, "src/data_generator.py": _BAD_DOCTEST}}
    rewrite = {"interfaces": {**_GOOD, "src/experiment.py": _GOOD["src/experiment.py"].replace("run_experiment()", "run_experiment(cfg)")}}
    orch, calls = _critic_orch(tmp_path, [{"status": "PASS", "issues": []}], [rewrite, {}])
    (_plan, interfaces, violations), patched = _patched(orch, lambda: orch._validated_plan(broken, {"user_prompt": "p"}, tmp_path / "planner.md"))
    assert interfaces == _GOOD and violations == [] and len(calls["planner"]) == 1
    assert patched[0]["accepted"] is True and patched[0]["changed"] == ["src/data_generator.py"]
    assert any("ENTRYPOINT_HAS_ARGUMENTS" in r for r in patched[0]["rejected"])


def test_a_patch_may_surface_a_problem_if_it_fixes_more(tmp_path: Path):
    """Fixing an import can uncover a doctest the stub import used to hide: progress, so it is applied."""
    broken = {**_PLAN, "interfaces": {**_GOOD, "src/data_generator.py": _BAD_DOCTEST,
                                      "src/experiment.py": _GOOD["src/experiment.py"].replace("run_experiment()", "run_experiment(cfg)")}}
    patch = {"interfaces": {"src/experiment.py": _GOOD["src/experiment.py"], "src/data_generator.py": _GOOD["src/data_generator.py"]}}
    orch, _calls = _critic_orch(tmp_path, [{"status": "PASS", "issues": []}], [patch])
    _, interfaces, violations = orch._validated_plan(broken, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert violations == [] and interfaces == _GOOD
