"""§XXI (2026-11-23): fałszywy `verified` (test bez asercji, funkcja bez `return`) i przeplanowanie, które widzi
kod zależności, poprawia czekający test i cofa jednego winnego sąsiada."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph.oracles import assertionless_tests, functions_without_return, static_defects
from adk.hypergraph.schedule import FAILED
from adk.orchestration.common import _RunState
from tests.test_audit_xi import _TASKS, _planned


def _state(tasks: list[dict]) -> _RunState:
    return _RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=tasks)


# --- guards of the write gate -----------------------------------------------------------------------------------


def test_a_test_of_comments_only_checks_nothing():
    src = "def test_a():\n    x = 1\n    # assert x\n\ndef test_b():\n    assert 1\n"
    assert assertionless_tests(src) == ["test_a"]


def test_every_kind_of_check_counts_as_an_assertion():
    src = (
        "import pytest\nimport numpy as np\n\n"
        "def _check(v):\n    assert v\n\n"
        "def test_raises():\n    with pytest.raises(ValueError):\n        int('x')\n\n"
        "def test_approx():\n    pytest.approx(1.0)\n\n"
        "def test_numpy():\n    np.testing.assert_allclose(1, 1)\n\n"
        "def test_helper():\n    _check(1)\n\n"
        "class TestK:\n    def test_m(self):\n        self.assertEqual(1, 1)\n"
    )
    assert assertionless_tests(src) == []


def test_a_nested_function_does_not_make_a_test_check_something():
    assert assertionless_tests("def test_a():\n    def inner():\n        assert 1\n") == ["test_a"]


def test_a_function_promising_a_value_without_return_is_found():
    src = "def f(n: int) -> int:\n    for _ in range(n):\n        pass\n"
    assert functions_without_return(src) == ["f"]


def test_functions_that_legitimately_have_no_return_value_pass():
    src = (
        "from abc import abstractmethod\nfrom typing import Iterator, NoReturn\n\n"
        "def none() -> None:\n    x = 1\n\n"
        "def untyped(n):\n    x = n\n\n"
        "def gen() -> Iterator[int]:\n    yield 1\n\n"
        "def fails() -> int:\n    x = 1\n    raise ValueError(x)\n\n"
        "def never() -> NoReturn:\n    x = 1\n\n"
        "def stub() -> int:\n    ...\n\n"
        "def nested() -> int:\n    def inner() -> int:\n        return 1\n    return inner()\n\n"
        "class A:\n    @abstractmethod\n    def m(self) -> int:\n        x = 1\n\n"
        "    def n(self) -> int:\n        return 2\n"
    )
    assert functions_without_return(src) == []


def test_a_return_only_in_a_nested_function_does_not_count():
    src = "def f() -> int:\n    def inner() -> int:\n        return 1\n    inner()\n"
    assert functions_without_return(src) == ["f"]


def test_static_defects_judge_by_the_kind_of_the_vertex(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "tests").mkdir()
    (orch.workspace_dir / "tests/test_core.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    (orch.workspace_dir / "config.py").write_text("def f() -> int:\n    x = 1\n", encoding="utf-8")
    assert [v.rule for v in static_defects(orch.workspace_dir, "tests/test_core.py", h)] == ["TEST_NO_ASSERTIONS"]
    assert [v.rule for v in static_defects(orch.workspace_dir, "config.py", h)] == ["FUNCTION_NEVER_RETURNS"]
    assert static_defects(orch.workspace_dir, "unplanned.py", h) == []


def test_static_defects_ignore_a_file_that_does_not_parse(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "config.py").write_text("def f(:\n", encoding="utf-8")
    assert static_defects(orch.workspace_dir, "config.py", h) == []


# --- re-plan ------------------------------------------------------------------------------------------------------


def _answer(orch, tasks: list[dict]) -> list[dict]:
    sent: list[dict] = []
    orch._call_agent = lambda _md, payload, **_k: sent.append(payload) or {"status": "ok", "output": {"tasks": tasks}}
    return sent


def test_the_dossier_carries_the_code_and_state_of_the_dependencies(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "config.py").write_text("X = 1\n", encoding="utf-8")
    h.vertices["config.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    sent = _answer(orch, [])
    orch._replan_failed(_state([]))
    deps = sent[0]["repair_dossier"]["failed"][0]["dependencies"]
    assert deps["config.py"] == {"state": "verified", "source": "X = 1\n"}


def test_a_waiting_test_of_a_failed_module_takes_the_fix_instead_of_dropping_it(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    queue = [{**_TASKS[2], "status": "WAITING"}]
    _answer(orch, [{"target_node": "tests/test_core.py", "description": "Pass an array, not 0", "assigned_agent": "seed_tester"}])
    result = orch._replan_failed(_state(queue))
    assert result["tasks"] == [] and queue[0]["description"] == "Pass an array, not 0" and queue[0]["force_ready"] is True


def test_a_fix_of_a_test_runs_once_although_its_module_is_not_verified(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    task = {**_TASKS[2], "status": "WAITING", "force_ready": True}
    state = _state([task])
    assert [t["task_id"] for _i, t in orch._task_order(state)][:1] == ["T3"]
    assert "force_ready" not in task
    task["status"] = "WAITING"
    assert list(orch._task_order(state)) == []  # the second time it waits for its module again


def test_a_new_test_task_of_a_failed_module_goes_first(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    _answer(orch, [
        {"target_node": "core.py", "description": "rewrite", "assigned_agent": "seed_coder"},
        {"target_node": "tests/test_core.py", "description": "fix the test", "assigned_agent": "seed_tester"},
    ])
    tasks = orch._replan_failed(_state([]))["tasks"]
    assert [t["target_node"] for t in tasks] == ["tests/test_core.py", "core.py"] and tasks[0]["force_ready"]


def test_one_verified_dependency_is_reopened_and_never_twice(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    _answer(orch, [{"target_node": "config.py", "description": "return the value", "assigned_agent": "seed_coder"}])
    result = orch._replan_failed(_state([]))
    assert [t["target_node"] for t in result["tasks"]] == ["config.py"] and h.vertices["config.py"].state == "stale"
    h.vertices["config.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    assert orch._replan_failed(_state([]))["tasks"] == [] and h.vertices["config.py"].state == "verified"


def test_a_verified_vertex_outside_the_dossier_stays_closed_and_only_one_is_reopened(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = "verified"
    h.vertices["tests/test_core.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    _answer(orch, [
        {"target_node": "tests/test_core.py", "description": "x", "assigned_agent": "seed_tester"},
        {"target_node": "config.py", "description": "y", "assigned_agent": "seed_coder"},
        {"target_node": "config.py", "description": "z", "assigned_agent": "seed_coder"},
    ])
    result = orch._replan_failed(_state([]))
    assert [t["target_node"] for t in result["tasks"]] == ["config.py"]
    assert h.vertices["tests/test_core.py"].state == "verified"


# --- przegląd testu po porażce modułu na tym samym teście (próg 1, §XXII U3) ---------------------------------------------------

_PYTEST_ON_TEST = "Pytest failure:\ntests\\test_core.py:40: in test_x\ncore.py:88: in f\nE IndexError: boom"


def _blamed_twice(h) -> None:
    h.vertices["core.py"].history[:] = [{"task_id": "T3", "issues": [_PYTEST_ON_TEST]}, {"task_id": "T3", "issues": [_PYTEST_ON_TEST]}]


def _blamed_once(h) -> None:
    h.vertices["core.py"].history[:] = [{"task_id": "T3", "issues": [_PYTEST_ON_TEST]}]


def test_a_test_is_reviewed_after_the_module_failed_on_it(tmp_path: Path):
    from adk.orchestration.failure_attribution import _test_to_review

    _orch_, h = _planned(tmp_path)
    assert _test_to_review(h, "core.py", set()) is None  # no failures yet
    _blamed_once(h)
    assert _test_to_review(h, "core.py", set()) == "tests/test_core.py"
    assert _test_to_review(h, "core.py", {("core.py", "tests/test_core.py")}) is None  # once per pair
    h.vertices["tests/test_core.py"].state = "verified"
    assert _test_to_review(h, "core.py", set()) is None  # a test that passed is not suspected
    h.vertices["tests/test_core.py"].state = "written"
    h.vertices["core.py"].history[0] = {"task_id": "T3", "issues": ["Ruff lint failure: core.py:1:1: F821 x"]}
    assert _test_to_review(h, "core.py", set()) is None  # failures of another kind do not count


def _repair_with(tmp_path: Path, max_retries: int):
    orch, h = _planned(tmp_path)
    _blamed_twice(h)
    built: list[dict] = []
    orch._execute_builder_step = lambda task, **_k: built.append(task)
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda *_a, **_k: False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder", "issues": [_PYTEST_ON_TEST], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {**_TASKS[1]}
    state = _state([task])
    state.max_retries = max_retries
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    return orch, built, task


def test_the_review_goes_to_the_author_of_the_test_once_and_costs_no_repair_attempt(tmp_path: Path):
    orch, built, task = _repair_with(tmp_path, max_retries=2)
    assert [b["target_node"] for b in built] == ["tests/test_core.py", "core.py", "core.py"]
    assert "check the test, not the module" in built[0]["description"] and "check the test" not in built[1]["description"]
    assert task["repair_attempts"] == 2  # the module's first repair came after the review as attempt 1 (the review took none)
    assert orch._reviewed_tests == {("core.py", "tests/test_core.py")}


# --- §XXII: wspólna kolejka przeglądu testów (zmiana σ + porażka) ---------------------------------------------------


def test_a_verified_test_is_reviewed_only_after_the_interface_of_its_module_changed(tmp_path: Path):
    from adk.orchestration.failure_attribution import _test_to_review

    orch, h = _planned(tmp_path)
    _blamed_once(h)
    h.vertices["tests/test_core.py"].state = "verified"
    assert _test_to_review(h, "core.py", set()) is None
    orch._reopen_test_review(h, "core.py")
    assert orch._pending_review == {("core.py", "tests/test_core.py")}
    assert _test_to_review(h, "core.py", orch._reviewed_tests, orch._pending_review) == "tests/test_core.py"


def test_a_changed_interface_allows_one_more_review_of_the_same_test(tmp_path: Path):
    from adk.orchestration.failure_attribution import _test_to_review

    orch, h = _planned(tmp_path)
    _blamed_once(h)
    pair = ("core.py", "tests/test_core.py")
    orch._reviewed_tests = {pair}
    assert _test_to_review(h, "core.py", orch._reviewed_tests) is None  # reviewed for this version of σ
    orch._reopen_test_review(h, "core.py")  # σ changed (SPEC_AMENDED)
    assert pair not in orch._reviewed_tests
    assert _test_to_review(h, "core.py", orch._reviewed_tests, orch._pending_review) == "tests/test_core.py"


def test_only_a_change_of_the_call_contract_counts_as_a_change_of_the_interface():
    from adk.orchestration.plan_change import _contract_changed

    old = 'def f(x: int) -> tuple[int, int]:\n    """Old."""\n    ...\n'
    docs = 'def f(x: int) -> tuple[int, int]:\n    """New words."""\n    ...\n'
    returns = 'def f(x: int) -> int:\n    """Old."""\n    ...\n'
    spec = {"symbols": {"f": {"kind": "func", "params": ["x"], "required": ["x"]}}}
    assert not _contract_changed(spec, spec, old, docs)
    assert _contract_changed(spec, spec, old, returns)
    assert _contract_changed(spec, {"symbols": {}}, old, old)


def test_a_review_that_changes_nothing_sends_the_next_repair_to_the_module(tmp_path: Path):
    orch, h = _planned(tmp_path)
    _blamed_once(h)
    built: list[dict] = []

    def _builder(task, **_k):
        built.append(task)
        if task["target_node"].startswith("tests/"):
            raise RuntimeError("the answer changes nothing")

    orch._execute_builder_step = _builder
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda *_a, **_k: False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder", "issues": [_PYTEST_ON_TEST], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {**_TASKS[1]}
    state = _state([task])
    state.max_retries = 2
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    assert [b["target_node"] for b in built] == ["tests/test_core.py", "core.py", "core.py"]  # the review took no attempt, the module follows
    assert orch._reviewed_tests == {("core.py", "tests/test_core.py")}


def test_a_replan_interface_for_a_module_outside_the_plan_is_logged_not_swallowed(tmp_path: Path, monkeypatch):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    events: list[tuple] = []
    monkeypatch.setattr(orch.logger, "log_event", lambda name, **kw: events.append((name, kw)))
    changed = orch._replan_interfaces(h, {"interfaces": {"new_helper.py": "def f() -> int:\n    ...\n"}}, ["core.py"], {}, {})
    assert changed == []
    assert [(n, kw["module"], kw["reason"]) for n, kw in events] == [("SPEC_AMEND_SKIPPED", "new_helper.py", "not a module of the plan")]


# --- §XXII U5: podpowiedź przy F821 -------------------------------------------------------------------------------


def test_an_undefined_constant_of_the_file_itself_is_hinted_from_its_own_interface(tmp_path: Path):
    from types import SimpleNamespace

    from adk.orchestration.findings import repair_findings
    from adk.orchestration.import_hints import importable_names, own_declarations

    own = SimpleNamespace(type="I", id="I:experiment.py", spec={"import": "experiment", "uses": {"subspace.py": ["Detector", "N"]}, "symbols": {
        "N_ESTIMATORS": {"kind": "const", "type": "int"}, "run": {"kind": "func"}}})
    producer = SimpleNamespace(type="I", id="I:subspace.py", spec={"import": "subspace", "symbols": {"N": {"kind": "const"}, "Detector": {"kind": "class"}}})
    other = SimpleNamespace(type="I", id="I:other.py", spec={"import": "other", "symbols": {"N": {"kind": "const"}}})  # makes `N` ambiguous
    h = SimpleNamespace(edges={e.id: e for e in (own, producer, other)})
    (tmp_path / "experiment.py").write_text("def run():\n    return N_ESTIMATORS + N\n", encoding="utf-8")
    issue = "Ruff lint failure: experiment.py:2:12: F821 Undefined name `N_ESTIMATORS`\nexperiment.py:2:29: F821 Undefined name `N`"
    texts = [f.text for f in repair_findings([issue], tmp_path, lambda rel: importable_names(h, rel, {}), lambda rel: own_declarations(h, rel))]
    assert "`N_ESTIMATORS: int` is declared by the planned interface of this file" in texts[0]
    assert "`from subspace import N`" in texts[1]  # the file's own `uses` settles the ambiguous name


# --- §XXIII: jedna reguła sąsiedztwa (w dół i w górę) i kontekst wywołania ---------------------------------------------


def test_a_caller_named_in_the_errors_of_a_failed_module_is_in_the_dossier_and_reopenable(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "core.py").write_text("def f(state):\n    return state\n", encoding="utf-8")
    h.vertices["config.py"].state = FAILED
    h.vertices["core.py"].state = "verified"  # core.py uses config.py: it is above it
    h.vertices["config.py"].history[:] = [{"task_id": "T1", "issues": ["Pytest failure:\ncore.py:3: in f\nconfig.py:1: in g\nE TypeError"]}]
    sent = _answer(orch, [{"target_node": "core.py", "description": "pass a tuple", "assigned_agent": "seed_coder"}])
    result = orch._replan_failed(_state([]))
    entry = sent[0]["repair_dossier"]["failed"][0]
    assert entry["dependents"]["core.py"]["state"] == "verified"
    assert [t["target_node"] for t in result["tasks"]] == ["core.py"] and h.vertices["core.py"].state == "stale"


def test_a_neighbour_the_errors_do_not_name_is_not_a_suspect(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = FAILED
    h.vertices["core.py"].state = "verified"
    h.vertices["config.py"].history[:] = [{"task_id": "T1", "issues": ["Ruff lint failure: config.py:1:1: F821 x"]}]
    sent = _answer(orch, [{"target_node": "core.py", "description": "x", "assigned_agent": "seed_coder"}])
    result = orch._replan_failed(_state([]))
    assert sent[0]["repair_dossier"]["failed"][0]["dependents"] == {} and result["tasks"] == []


def test_a_file_name_inside_another_name_is_not_a_mention():
    from adk.orchestration.fragment_replan import _mentioned

    assert _mentioned("tests\\test_trainer.py:13: in test_x\ntrainer.py:63: in f", "trainer.py")
    assert not _mentioned("tests\\test_trainer.py:13: in test_x", "trainer.py")
    assert _mentioned("tests\\test_trainer.py:13: in test_x", "tests/test_trainer.py")


def test_a_test_of_another_module_named_in_the_failures_is_reviewed_too(tmp_path: Path):
    from adk.orchestration.failure_attribution import _test_to_review

    _orch_, h = _planned(tmp_path)
    foreign = "Pytest failure:\ntests\\test_other.py:5: in test_y\ncore.py:9: in f\nE TypeError: unhashable"
    h.vertices["core.py"].history[:] = [{"task_id": "T3", "issues": [foreign]}]
    from adk.hypergraph.model import Vertex

    h.vertices["tests/test_other.py"] = Vertex(id="tests/test_other.py", kind="test", owner=None, state="written")
    assert _test_to_review(h, "core.py", set()) == "tests/test_other.py"
    h.vertices["tests/test_other.py"].state = "verified"
    assert _test_to_review(h, "core.py", set()) is None


def test_a_pytest_finding_shows_the_call_that_passed_the_argument(tmp_path: Path):
    from adk.orchestration.findings import repair_findings

    (tmp_path / "tests").mkdir()
    (tmp_path / "trainer.py").write_text("def train(agent):\n    state = [1, 2]\n    agent.update(state)\n", encoding="utf-8")
    (tmp_path / "agent.py").write_text("class A:\n    def update(self, s):\n        return s in {}\n", encoding="utf-8")
    (tmp_path / "tests/test_trainer.py").write_text("def test_t():\n    pass\n", encoding="utf-8")
    issue = (
        "Pytest failure:\n_____ test_t _____\ntests/test_trainer.py:2: in test_t\n    train(A())\n"
        "trainer.py:3: in train\n    agent.update(state)\nagent.py:3: in update\n    return s in {}\nE TypeError: unhashable type: 'list'\n"
    )
    [finding] = repair_findings([issue], tmp_path)
    assert finding.file == "agent.py" and "called from trainer.py:3 (`agent.update(state)`)" in finding.text
    direct = issue.replace("trainer.py:3: in train\n    agent.update(state)\n", "")
    assert "called from" not in repair_findings([direct], tmp_path)[0].text  # the test itself called the code


# --- §XXIII: interfejs z typami i docstringami w kontekście agentów ---------------------------------------------------


def test_the_used_part_of_an_interface_is_the_named_definitions_with_their_docstrings():
    from adk.orchestration.interface_view import used_part

    src = (
        'import numpy as np\n\nN: int = 3\n\nclass A:\n    """A."""\n    def f(self) -> tuple[int, int]:\n        """Pair."""\n        ...\n\n'
        'def g(x: int) -> int:\n    """G."""\n    ...\n\ndef h() -> None:\n    ...\n'
    )
    part = used_part(src, ["A", "g"])
    assert "def f(self) -> tuple[int, int]" in part and '"""Pair."""' in part and "def g(x: int) -> int" in part
    assert "def h" not in part and "N: int" not in part
    assert "def h" in used_part(src, [])  # no names: the whole interface


def test_the_tester_reads_the_full_interface_of_the_module_under_test(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    blueprint = {"interfaces": {"core.py": "def f() -> tuple[int, int]:\n    \"\"\"Pair.\"\"\"\n    ...\n"}}
    orch.blueprint_path.write_text(__import__("json").dumps(blueprint), encoding="utf-8")
    context = orch._context_for("tests/test_core.py", "tests/test_core.py")
    assert "def f() -> tuple[int, int]" in context["specification"]["core.py"]["interface"]
    assert "symbols" in context["specification"]["core.py"]  # σ stays


def test_the_coder_reads_only_what_it_uses_of_its_dependencies(tmp_path: Path):
    orch, h = _planned(tmp_path)
    uses = h.edges["I:core.py"].spec.get("uses", {})
    assert "config.py" in uses  # the fixture's core.py uses config.py
    blueprint = {"interfaces": {
        "config.py": "".join(f"{n}: int = 1\n" for n in uses["config.py"]) + "OTHER: int = 2\n",
        "core.py": "def own() -> None:\n    ...\n",
    }}
    orch.blueprint_path.write_text(__import__("json").dumps(blueprint), encoding="utf-8")
    spec = orch._context_for("core.py", "core.py")["specification"]
    assert "OTHER" not in spec["config.py"]["interface"] and uses["config.py"][0] in spec["config.py"]["interface"]
    assert "interface" not in spec["core.py"]  # its own stub is in `existing_content`
