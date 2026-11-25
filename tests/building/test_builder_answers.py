"""How the harness reads what a builder answers: wrong shapes, JSON that is no JSON, content that lands nowhere, a coder that touches a test, a task echoed back, a failed model call as an answer."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from adk.core.llm import _extract_json_from_text
from adk.orchestration.common import MaterializationError
from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.adk_sandbox import _clone_adk_env
from tests.support.config_module_source import CONFIG
from tests.support.orchestrator_sandbox import _orch
from tests.support.results_pointer_workspace import _CSV, _report, _workspace


def _events(orch: NeuroSymbolicOrchestrator) -> list[dict]:
    return json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]


TEST = "def test_x() -> None:\n    assert True\n"


CODER = {"agent": "seed_coder", "task_id": "T20_FIX1"}


def test_files_as_a_path_to_content_mapping_is_saved(tmp_path: Path) -> None:
    """R3: 01 R1_2_FIX2 "the fields ['files'] match no allowed shape" for an otherwise clear answer."""
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact("config.py", {"files": {"config.py": CONFIG}})
    assert (orch.workspace_dir / "config.py").read_text(encoding="utf-8") == CONFIG


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


def test_an_answer_that_is_no_json_is_told_so() -> None:
    """01/02: a cut-off answer was told its fields ['error', 'issues', 'raw_response'] match no shape."""
    from adk.orchestration import agent_texts as texts

    assert "not valid JSON" in texts.unknown_answer_shape("src/a.py", ["error", "issues", "raw_response"], {})


def test_a_prose_repair_that_breaks_the_experiment_is_restorable(tmp_path: Path):
    from adk.orchestration.building import BuildingMixin

    ws = _workspace(tmp_path)
    (ws / "experiment.py").write_text("OLD = 1\n", encoding="utf-8")
    me = SimpleNamespace(workspace_dir=ws, _last_experiment_error="")
    guard = BuildingMixin._guard_results_from_prose_fix(me, _report([]), "experiment.py")
    assert guard is not None
    (ws / "experiment.py").write_text("BROKEN = 2\n", encoding="utf-8")
    (ws / "results.csv").unlink()
    BuildingMixin._restore_files(me, guard)
    assert (ws / "experiment.py").read_text(encoding="utf-8") == "OLD = 1\n"
    assert (ws / "results.csv").read_text(encoding="utf-8") == _CSV
    # Not a document failure, no results, or the experiment already failing: nothing to guard.
    assert BuildingMixin._guard_results_from_prose_fix(me, {"failed_file": "agent.py"}, "experiment.py") is None
    me._last_experiment_error = "KeyError"
    assert BuildingMixin._guard_results_from_prose_fix(me, _report([]), "experiment.py") is None


def test_robust_json_extraction_with_think_tags_and_prose():
    noisy_output = (
        "<think>\nLet me analyze the hypergraph blast radius first.\n</think>\n"
        "Here is the required JSON output:\n"
        "```json\n"
        '{"status": "PASS", "approved": true, "issues": []}\n'
        "```\n"
        "Hope this helps!"
    )
    parsed = _extract_json_from_text(noisy_output)
    assert isinstance(parsed, dict)
    assert parsed["status"] == "PASS"
    assert parsed["approved"] is True


def test_materialization_raises_when_agent_content_lands_nowhere(tmp_path: Path):
    import pytest

    from adk.orchestrator import MaterializationError

    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    orch.provider = "ollama"  # the guard is disabled for the mock fallback path
    with pytest.raises(MaterializationError):
        orch._materialize_workspace_artifact("results.csv", {"source_code": "def plot():\n    return 1\n"})


def test_materialization_accepts_files_list_for_any_path(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    orch.provider = "ollama"
    orch._materialize_workspace_artifact(
        "results.csv", {"files": [{"filename": "plot_results.py", "content": "def plot():\n    return 1\n"}]}
    )
    assert (adk_dir / "workspace" / "plot_results.py").exists()


def test_coder_cannot_rewrite_a_test_but_keeps_the_rest_of_its_answer(tmp_path: Path) -> None:
    """N2: the coder fixed failed assertions by rewriting the test (7x CROSS_ROLE_WRITE)."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "test_experiment.py").write_text(TEST, encoding="utf-8")

    orch._materialize_workspace_artifact(
        "experiment.py",
        {"files": [
            {"filename": "experiment.py", "content": "X = 1\n"},
            {"filename": "test_experiment.py", "content": "def test_x() -> None:\n    pass\n"},
        ]},
        writer=CODER,
    )

    assert (orch.workspace_dir / "experiment.py").read_text(encoding="utf-8") == "X = 1\n"
    assert (orch.workspace_dir / "test_experiment.py").read_text(encoding="utf-8") == TEST
    assert any(e["type"] == "CODER_TEST_WRITE_SKIPPED" for e in _events(orch))


def test_coder_answer_that_only_touches_a_test_is_refused_with_the_reason(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    (orch.workspace_dir / "test_experiment.py").write_text(TEST, encoding="utf-8")

    with pytest.raises(MaterializationError, match="belong to the tester"):
        orch._materialize_workspace_artifact(
            "experiment.py",
            {"ast_edits": [{"symbol": "test_x", "file": "test_experiment.py", "code": "def test_x() -> None:\n    pass\n"}]},
            writer=CODER,
        )
    assert (orch.workspace_dir / "test_experiment.py").read_text(encoding="utf-8") == TEST


def test_tester_still_writes_tests(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact(
        "test_env.py", {"files": [{"filename": "test_env.py", "content": TEST}]},
        writer={"agent": "seed_tester", "task_id": "T9"},
    )
    assert (orch.workspace_dir / "test_env.py").exists()


def test_workspace_prefix_is_stripped_and_a_test_lands_in_its_existing_file(tmp_path: Path) -> None:
    """N3: `workspace/tests/test_experiment.py` created a nested workspace/ and duplicate tests appeared."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "tests").mkdir()
    (orch.workspace_dir / "tests" / "test_experiment.py").write_text(TEST, encoding="utf-8")
    new = "def test_y() -> None:\n    assert True\n"

    orch._materialize_workspace_artifact(
        "tests/test_experiment.py",
        {"files": [
            {"filename": "workspace/src/run.py", "content": "Y = 2\n"},
            {"filename": "test_experiment.py", "content": new},
        ]},
        writer={"agent": "seed_tester", "task_id": "T21"},
    )

    assert (orch.workspace_dir / "src" / "run.py").exists()
    assert not (orch.workspace_dir / "workspace").exists()
    assert (orch.workspace_dir / "tests" / "test_experiment.py").read_text(encoding="utf-8") == new
    assert not (orch.workspace_dir / "test_experiment.py").exists()


def test_ast_edits_on_a_document_and_malformed_elements_get_a_clear_reason(tmp_path: Path) -> None:
    """N7: ast_edits on thesis.md answered 'SyntaxError in new_code'; a malformed element vanished."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "thesis.md").write_text("# Praca\n", encoding="utf-8")

    with pytest.raises(MaterializationError, match=r"only for \.py files.*'sections'"):
        orch._materialize_workspace_artifact(
            "thesis.md", {"ast_edits": [{"symbol": "LastSection", "file": "thesis.md", "code": "## X\ntekst\n"}]}
        )
    with pytest.raises(MaterializationError, match=r"without the required 'symbol' or 'code'.*\['content', 'name'\]"):
        orch._materialize_workspace_artifact("a.py", {"ast_edits": [{"name": "f", "content": "def f(): pass"}]})


def test_task_echoed_back_in_the_answer_is_ignored(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact(
        "a.py", {"task": {"task_id": "T1"}, "files": [{"filename": "a.py", "content": "A = 1\n"}]}
    )
    assert (orch.workspace_dir / "a.py").exists()
