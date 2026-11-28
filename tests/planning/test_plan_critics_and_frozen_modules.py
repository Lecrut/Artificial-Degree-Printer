"""What the planning critics see and how they block: the interface without bodies, an accepted consumer that does or does not pin a name, a consumer reopened after an outline revision."""

from __future__ import annotations

from pathlib import Path

from adk.mocks.staged import sketch_of

_BASELINE = 'class RandomAgent:\n    """Plays at random."""\n\n    def act(self, state: int) -> int:\n        """Pick an action."""\n        ...\n'


_EXPERIMENT = (
    "from baseline import evaluate_random_agent\n\n\n"
    'def run_experiment() -> None:\n    """Run."""\n    evaluate_random_agent(1)\n'
)


def _two_module_outline(baseline_provides: list[str]) -> dict:
    from adk.orchestration.planning.outline import outline_of

    outline = outline_of({
        "modules": [
            {"file": "baseline.py", "purpose": "baseline", "depends_on": [], "provides": baseline_provides},
            {"file": "experiment.py", "purpose": "run", "depends_on": ["baseline.py"], "provides": ["run_experiment() -> None"]},
        ],
        "entrypoint": "experiment.py:run_experiment", "plots": "", "academic_blueprint": {},
    })
    assert outline is not None
    return outline


def test_the_module_critic_sees_the_interface_without_a_written_body(tmp_path: Path) -> None:
    from tests.support.staged_planning import _MOD_A, _base_plan, _make_orch, _run

    seen: list[str] = []
    with_body = 'def helper_a() -> int:\n    """Return 1."""\n    import csv\n    return csv.QUOTE_ALL\n'

    def critic(payload: dict, _n: int) -> dict:
        seen.append(payload.get("source", ""))
        return {"status": "PASS", "issues": []}

    plan = _base_plan()
    plan["interfaces"]["src/mod_a.py"] = with_body
    (_result, _calls) = _run(_make_orch(tmp_path), plan, {"module_critic_guard": critic})
    assert any("def helper_a" in s for s in seen) and not any("csv" in s for s in seen)
    assert _MOD_A  # the fixture the plan stages tests share is untouched


def test_a_promise_written_with_a_keyword_is_the_name_after_it() -> None:
    from adk.orchestration.planning.outline import provided_name

    assert provided_name("class ZScoreDetector: <Class>") == "ZScoreDetector"
    assert provided_name("def run() -> None") == "run"
    assert provided_name("async def fetch(x)") == "fetch"
    assert provided_name("const SEED = 3") == "SEED"
    assert provided_name("ZScoreDetector.fit(X: np.ndarray) -> None") == "ZScoreDetector.fit"
    assert provided_name("classify(x)") == "classify"  # a name that only starts like a keyword


def test_an_accepted_consumer_does_not_pin_a_name_the_outline_no_longer_promises(tmp_path: Path) -> None:
    from tests.support.staged_planning import _make_orch

    orch = _make_orch(tmp_path)
    accepted = {"experiment.py": _EXPERIMENT}
    outline = _two_module_outline(["RandomAgent()", "RandomAgent.act(state) -> int"])
    problems = orch._module_problems("baseline.py", _BASELINE, accepted, outline, {})
    assert not any("already imports" in p for p in problems)  # the consumer is reopened at its own turn instead


def test_an_accepted_consumer_still_pins_a_name_the_outline_promises(tmp_path: Path) -> None:
    from tests.support.staged_planning import _make_orch

    orch = _make_orch(tmp_path)
    outline = _two_module_outline(["RandomAgent()", "evaluate_random_agent(n) -> dict"])
    problems = orch._module_problems("baseline.py", _BASELINE, {"experiment.py": _EXPERIMENT}, outline, {})
    assert any("already imports evaluate_random_agent" in p for p in problems)


def test_reopened_consumer_does_not_block_dependency_after_outline_revision(tmp_path: Path) -> None:
    from adk.orchestration.planning.outline import outline_of
    from tests.support.staged_planning import _make_orch

    orch = _make_orch(tmp_path)
    old = outline_of({
        "modules": [
            {"file": "base.py", "purpose": "Base.", "depends_on": [], "provides": ["old_fn() -> int"]},
            {"file": "exp.py", "purpose": "Exp.", "depends_on": ["base.py"], "provides": ["run() -> None"]},
        ],
        "entrypoint": "exp.py:run", "plots": "exp.py:run",
        "academic_blueprint": {"thesis_title": "T", "thesis_statement": "S", "baseline_comparison": "B", "metrics": ["m"]},
    })
    new = outline_of({
        "modules": [
            {"file": "base.py", "purpose": "Base.", "depends_on": [], "provides": ["new_fn() -> int"]},
            {"file": "exp.py", "purpose": "Exp.", "depends_on": ["base.py"], "provides": ["run() -> None"]},
        ],
        "entrypoint": "exp.py:run", "plots": "exp.py:run",
        "academic_blueprint": {"thesis_title": "T", "thesis_statement": "S", "baseline_comparison": "B", "metrics": ["m"]},
    })
    assert old is not None and new is not None
    accepted = {
        "base.py": 'def old_fn() -> int:\n    """Old."""\n    ...\n',
        "exp.py": 'from base import old_fn\ndef run() -> None:\n    """Run."""\n    ...\n',
    }
    reopen: dict[str, list[str]] = {}
    revised = orch._revise_outline(old, new, accepted, reopen)

    def module_author(payload: dict, _n: int) -> dict:
        rel = payload["module"]["file"]
        if rel == "base.py":
            return {**sketch_of('def new_fn() -> int:\n    """New."""\n    ...\n'), "needs": {}}
        return {**sketch_of('from base import new_fn\ndef run() -> None:\n    """Run."""\n    ...\n'), "needs": {}}

    orch._call_agent = lambda md, payload, **_k: (
        {"status": "ok", "output": module_author(payload, 0)} if "plan_module" in str(md)
        else {"status": "ok", "output": {"status": "PASS", "issues": []}}
    )
    ok, _failed, problems = orch._settle({"user_prompt": "T", "available_packages": [], "experiment_time_limit_s": 60}, revised, accepted, {}, reopen)
    assert ok and problems == []
    assert "new_fn" in accepted["base.py"] and "new_fn" in accepted["exp.py"]


def test_the_critics_read_every_body_as_an_ellipsis() -> None:
    from adk.orchestration.building.interface_view import interface_view

    source = 'class A:\n    """Doc."""\n\n    def go(self, x: int) -> int:\n        """Go."""\n        return x + 1\n'
    view = interface_view(source)
    assert "NotImplementedError" not in view and "return x + 1" not in view and "..." in view and '"""Go."""' in view
