"""How findings are classified and compared: fingerprints that ignore names and line numbers, categories (ruff code, pytest exception, syntax, harness), what is a warning and what blocks, findings fitted whole to the budget."""

from __future__ import annotations

from pathlib import Path

from adk.orchestration import agent_texts as texts
from adk.orchestration.verification.failure_kinds import _issue_category
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.verification import run_isolated_tests
from tests.support.adk_sandbox import _clone_adk_env
from tests.support.run_loop_fixtures import _RUFF_F841


def test_categories_evolution_can_learn_from() -> None:
    """E2: concise ruff findings and experiment tracebacks fell into `generic`."""
    assert _issue_category(["Ruff lint failure: src\\experiment_runner.py:35:20: F821 Undefined name `config`"]) == "F821"
    trace = 'Traceback (most recent call last):\n  File "x.py", line 1, in <module>\nTypeError: boxplot() got labels'
    assert _issue_category([trace]) == "run:TypeError"
    assert _issue_category(["something nobody recognises"]) == "generic"


def test_failure_category_ignores_the_file() -> None:
    a = ["Pytest failure: FAILED test_game.py::test_reset - AssertionError"]
    b = ["Pytest failure: FAILED test_env.py::test_step - AssertionError"]
    assert _issue_category(a) == _issue_category(b) == "pytest:AssertionError"
    assert _issue_category(["Syntax error in game.py: invalid syntax"]) == "SyntaxError"


def test_every_gate_rejection_wrapper_is_harness_not_generic_and_outweighs_quoted_errors() -> None:
    """§VI.9 P2: two of the three builder-exception wrappers fell into `generic` (2026-11-14)."""
    for wrapper in (
        texts.task_exception("T3", "n2", "a.py", texts.spec_breach(["API_MISSING [a.py]: f"], [])),
        texts.fast_repair_exception("T3_FIX1", "a.py", texts.symbol_edits_rejected(["a.py:f: SyntaxError"])),
        texts.repair_task_exception("T3_FIX", "n2", "a.py", texts.unparsable_code(["a.py:3: invalid syntax"])),
    ):
        assert _issue_category([wrapper]) == "harness", wrapper
    assert _issue_category(["Import contract violation: env.py imports TicTacToe from game.py"]) == "contract"
    assert _issue_category(["Unresolved pointer: \\ref_ast{x.py:Y} (Source file 'x.py' does not exist)"]) == "document"


def test_collect_report_issues_reads_supervisor_issues():
    from adk.orchestrator import _collect_report_issues

    report = {
        "status": "FAIL",
        "supervisors": {
            "code_auditor": {"status": "FAIL", "issues": ["Pytest failure: AttributeError: module 'core' has no attribute 'x'"]},
            "symbolic_auditor": {"status": "SKIPPED_OUT_OF_EDGE_SCOPE", "issues": []},
            "redteam_critic_guard": {"status": "FAIL", "issues": ["Pytest failure: AttributeError: module 'core' has no attribute 'x'"]},
        },
        "issues": ["builder crashed"],
    }
    assert _collect_report_issues(report) == [
        "builder crashed",
        "Pytest failure: AttributeError: module 'core' has no attribute 'x'",
    ]
    assert _collect_report_issues({"status": "PASS"}) == []


def test_real_pytest_errors_come_first_in_code_audit(tmp_path: Path, monkeypatch):
    import adk.orchestrator as orch_mod

    real_call_agent = orch_mod.call_agent

    def fake_call_agent(agent_md, payload, *args, **kwargs):
        if "code_auditor" in str(agent_md):
            return {"output": {"status": "FAIL", "issues": ["LLM paraphrase of the failure"]}}
        return real_call_agent(agent_md, payload, *args, **kwargs)

    monkeypatch.setattr(orch_mod, "call_agent", fake_call_agent)
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=True, provider="mock")
    ws = adk_dir / "workspace"
    (ws / "core.py").write_text("def get_board():\n    return []\n", encoding="utf-8")
    (ws / "tests").mkdir(exist_ok=True)
    (ws / "tests" / "test_core.py").write_text(
        "import core\n\n\ndef test_missing():\n    assert core.is_terminal([])\n", encoding="utf-8"
    )
    from tests.support.planned_projects import with_plan

    with_plan(
        orch, {"core.py": '"""Core."""\n\n\ndef get_board() -> list:\n    """Board."""\n'}, None,
        [{"task_id": "T5", "target_node": "tests/test_core.py", "description": "tests", "assigned_agent": "seed_tester"}],
    )
    task = {"task_id": "T5", "target_node": "tests/test_core.py", "assigned_agent": "seed_tester", "status": "IN_PROGRESS"}

    report = orch._run_verification_step(task, include_docs=True, is_final_gate=False)

    assert report["status"] == "FAIL"
    issues = report["supervisors"]["code_auditor"]["issues"]
    assert "is_terminal" in issues[0]
    # An intermediate task is judged on the deterministic findings alone; the LLM auditor reads only at Gate 3.
    assert "LLM paraphrase of the failure" not in issues
    assert report["supervisors"]["code_auditor"]["skipped"] == "deterministic_only"
    # The test reads a name the interface of core.py does not declare: σ names the exact violation (I bag in H).
    assert any("IMPORT_OUTSIDE_SPEC" in v and "is_terminal" in v for v in report["contract_violations"])


def test_issue_signature_ignores_renamed_identifiers_and_line_numbers():
    from adk.orchestrator import _issue_signature

    sigs = {
        _issue_signature({"issues": [_RUFF_F841.format(name=name, line=line)]})
        for name, line in (("width", 19), ("bars", 24), ("plot_df", 17))
    }
    assert sigs == {"plot_results.py:F841"}


def test_issue_signature_distinguishes_files_and_rules():
    from adk.orchestrator import _issue_signature

    a = _issue_signature({"issues": [_RUFF_F841.format(name="x", line=1)]})
    b = _issue_signature({"issues": [_RUFF_F841.format(name="x", line=1).replace("plot_results.py", "core.py")]})
    assert a != b


def test_mechanical_lint_is_a_warning_and_verification_never_edits(tmp_path: Path):
    """D3 (2026-11-15): who diagnoses does not edit. A mechanical finding does not block and the file stays
    exactly as its author wrote it."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    source = "def plot(values):\n    width = 0.35\n    return sum(values)\n"
    (ws / "plot_results.py").write_text(source, encoding="utf-8")
    res = run_isolated_tests(ws, verification_dir=tmp_path / "no_validators")
    assert res["ruff_passed"] is True
    assert not any("F841" in err for err in res["errors"])
    assert any("F841" in w for w in res["lint_warnings"])
    assert (ws / "plot_results.py").read_text(encoding="utf-8") == source


def test_blocking_lint_still_fails_verification(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "core.py").write_text("def run():\n    return undefined_name + 1\n", encoding="utf-8")
    res = run_isolated_tests(ws, verification_dir=tmp_path / "no_validators")
    assert res["ruff_passed"] is False
    assert any("F821" in err for err in res["errors"])


def test_findings_are_fitted_whole_with_a_count_note():
    from adk.orchestrator import _fit_items

    items = ["a" * 50, "b" * 50, "c" * 50]
    shown = _fit_items(items, max_chars=110)
    assert shown[:2] == items[:2]
    assert shown[-1].startswith("[showing 2 of 3")


def test_category_uses_the_full_exception_name_not_the_truncated_summary() -> None:
    """N4: the short summary cut names to 'AssertionEr...'; one failure became several categories."""
    truncated = (
        "Pytest failure: F\n___ test_run ___\ntest_e.py:3: in test_run\n    assert f()\n"
        "E   AssertionError: no results\nFAILED test_e.py::test_run - AssertionEr...\n"
    )
    assert _issue_category([truncated]) == "pytest:AssertionError"
