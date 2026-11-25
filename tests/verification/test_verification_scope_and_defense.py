"""Which verification applies to a task: a task is judged on its own node, an intermediate task ignores what is still to come, the final defense checks everything and only the red team's verdict can fail it."""

from __future__ import annotations

import json
from pathlib import Path

from adk.mocks import code_fixtures as fx
from adk.mocks.scenarios import config_source
from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.adk_sandbox import _clone_adk_env
from tests.support.failed_vertex_project import _planned
from tests.support.orchestrator_sandbox import _orch
from tests.support.phased_orchestrator import _setup_test_orchestrator
from tests.support.workspace_files import _write


def test_intermediate_task_ignores_pending_future_dependencies(tmp_path: Path) -> None:
    """Verify that intermediate tasks (is_final_gate=False) do not fail due to unmaterialized future task files."""
    orch = _setup_test_orchestrator(tmp_path)

    tasks = [
        {"task_id": "T1", "target_node": "thesis.md", "assigned_agent": "background_researcher", "status": "IN_PROGRESS"},
        {"task_id": "T2", "target_node": "config.py", "assigned_agent": "seed_coder", "status": "TODO"},
        {"task_id": "T3", "target_node": "core.py", "assigned_agent": "seed_coder", "status": "TODO"},
        {"task_id": "T4", "target_node": "results.csv", "assigned_agent": "seed_tester", "status": "TODO"},
        {"task_id": "T5", "target_node": "thesis.md", "assigned_agent": "seed_writer", "status": "TODO"},
    ]
    orch.task_queue_path.write_text(json.dumps(tasks), encoding="utf-8")

    doc_path = orch.workspace_dir / "thesis.md"
    doc_path.write_text(
        "# Wstęp\nParametr: \\ref_ast{config.py:ALPHA}, wynik: \\ref_csv{results.csv:accuracy}.\n",
        encoding="utf-8",
    )

    report = orch._run_verification_step(tasks[0], include_docs=True, is_final_gate=False)
    assert report["status"] == "PASS"

    val_data = json.loads(orch.validation_report_path.read_text(encoding="utf-8"))
    assert val_data["status"] == "PASS"
    assert val_data["supervisors"]["redteam_critic_guard"]["status"] == "SKIPPED_INTERMEDIATE_TASK"


def test_final_defense_gate_enforces_all_references_and_redteam(tmp_path: Path) -> None:
    """Verify that Gate 3 final defense (is_final_gate=True) strictly validates missing files and runs redteam."""
    orch = _setup_test_orchestrator(tmp_path)

    tasks = [
        {"task_id": "T1", "target_node": "thesis.md", "assigned_agent": "background_researcher", "status": "DONE"},
        {"task_id": "T2", "target_node": "config.py", "assigned_agent": "seed_coder", "status": "DONE"},
        {"task_id": "T3", "target_node": "core.py", "assigned_agent": "seed_coder", "status": "DONE"},
        {"task_id": "T4", "target_node": "results.csv", "assigned_agent": "seed_tester", "status": "DONE"},
        {"task_id": "T5", "target_node": "thesis.md", "assigned_agent": "seed_writer", "status": "DONE"},
    ]
    orch.task_queue_path.write_text(json.dumps(tasks), encoding="utf-8")

    doc_path = orch.workspace_dir / "thesis.md"
    doc_path.write_text("# Wstęp\nParametr: \\ref_ast{config.py:ALPHA}\n", encoding="utf-8")

    report = orch._run_verification_step(tasks[-1], include_docs=True, is_final_gate=True)
    assert report["status"] == "FAIL"

    val_data = json.loads(orch.validation_report_path.read_text(encoding="utf-8"))
    assert val_data["status"] == "FAIL"
    assert val_data["supervisors"]["symbolic_auditor"]["status"] == "FAIL"


def test_model_auditors_cannot_fail_the_defense_their_findings_are_warnings(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    orch.include_docs = False
    (orch.workspace_dir / "config.py").write_text(config_source(fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    opinions = {
        "code_auditor.md": {"status": "FAIL", "issues": ["the code looks fragile"]},
        "redteam_critic_guard.md": {"status": "FAIL", "gate_3_approved": False, "issues": ["the thesis overclaims"]},
    }
    orch._call_agent = lambda md, *_a, **_k: {"status": "ok", "output": dict(opinions.get(Path(md).name, {"status": "PASS", "issues": []}))}
    report = orch._run_verification_step({"task_id": "FINAL", "target_node": "core.py"}, include_docs=False, is_final_gate=True)
    assert report["status"] == "PASS"
    assert {"the code looks fragile", "the thesis overclaims"} <= set(report["warnings"])


def test_the_defense_approval_is_the_red_teams_alone(tmp_path: Path) -> None:
    orch, _h = _planned(tmp_path)
    orch.include_docs = False
    (orch.workspace_dir / "config.py").write_text(config_source(fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    vetoes = {"code_auditor.md": {"status": "PASS", "gate_3_approved": False, "issues": []}}
    orch._call_agent = lambda md, *_a, **_k: {"status": "ok", "output": dict(vetoes.get(Path(md).name, {"status": "PASS", "issues": []}))}
    report = orch._run_verification_step({"task_id": "FINAL", "target_node": "core.py"}, include_docs=False, is_final_gate=True)
    assert report["status"] == "PASS"


def test_gate_3_does_not_send_a_missing_pdf_back_to_the_writer(tmp_path: Path):
    """A missing thesis.pdf is the publisher's job. Gate 3 must not fail the thesis over it."""
    import shutil

    from adk.orchestrator import NeuroSymbolicOrchestrator

    src_adk = Path(__file__).resolve().parent.parent.parent / "adk"
    dst_adk = tmp_path / "adk"
    shutil.copytree(src_adk / "state", dst_adk / "state")
    shutil.copytree(src_adk / "agents", dst_adk / "agents")
    shutil.copytree(src_adk / "tools", dst_adk / "tools")
    ws = dst_adk / "workspace"
    ws.mkdir(parents=True, exist_ok=True)

    # Seed valid code and test
    (ws / "config.py").write_text("ALPHA = 0.1\n", encoding="utf-8")
    (ws / "core.py").write_text("def run(): pass\n", encoding="utf-8")
    (ws / "test_core.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    (ws / "results.csv").write_text("method,score\nbaseline,0.5\nproposed,0.9\n", encoding="utf-8")
    (ws / "references.bib").write_text("@article{key1, author={Author}, title={Title}, year={2024}}\n", encoding="utf-8")
    (ws / "thesis.md").write_text(
        "## Rozdział 1: Wstęp\nCel \\ref_ast{config.py:ALPHA}.\n"
        "## Rozdział 2: SOTA\nPrzegląd \\cite{key1}.\n"
        "## Rozdział 3: Architektura\nModel.\n"
        "## Rozdział 4: Implementacja\nKod.\n"
        "## Rozdział 5: Wyniki\nWyniki \\ref_csv{results.csv:score}.\n"
        "## Rozdział 6: Podsumowanie\nWnioski.\n",
        encoding="utf-8",
    )

    orch = NeuroSymbolicOrchestrator(adk_root=dst_adk, enable_layer4=False, include_docs=True, provider="mock")
    defense_task = {"task_id": "GATE_3_DEFENSE", "target_node": "thesis.md", "assigned_agent": "seed_writer"}

    report = orch._run_verification_step(defense_task, include_docs=True, is_final_gate=True)
    assert report["status"] == "PASS"
    all_issues = " ".join(report.get("issues", []))
    assert "thesis.pdf" not in all_issues.lower()


def test_mock_queue_does_not_compile_pdf(tmp_path: Path):
    from adk.orchestrator import NeuroSymbolicOrchestrator

    orch = NeuroSymbolicOrchestrator(adk_root=tmp_path, enable_layer4=False, provider="mock")
    assert orch._pdf_failure_report() is None


def test_edge_scoped_verification_skips_symbolic_auditor_for_v1(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=True, provider="mock")

    # Prepare workspace where results.csv is older than config.py; editing v1 should NOT fail on stale_csv_files
    ws = adk_dir / "workspace"
    (ws / "config.py").write_text("ALPHA: float = 0.2\n", encoding="utf-8")
    (ws / "results.csv").write_text("method,win_rate\nbaseline,0.5\nproposed,0.8\n", encoding="utf-8")

    v1_task = {
        "task_id": "T1",
        "description": "Edit config.py parameters",
        "target_node": "config.py",
        "assigned_agent": "seed_coder",
        "status": "IN_PROGRESS",
    }
    report_v1 = orch._run_verification_step(v1_task, include_docs=True, is_final_gate=False)
    assert report_v1["status"] == "PASS"
    assert report_v1["supervisors"]["symbolic_auditor"]["status"] == "SKIPPED_OUT_OF_EDGE_SCOPE"
    assert report_v1["supervisors"]["redteam_critic_guard"]["status"] == "SKIPPED_OUT_OF_EDGE_SCOPE"


def test_a_task_passes_despite_a_broken_file_it_does_not_own(tmp_path: Path) -> None:
    """2026-11-13: T7-T9 had correct modules and were FAILED because of three broken siblings."""
    orch = _orch(tmp_path)
    ws = orch.workspace_dir
    _write(ws, "src/__init__.py", "")
    _write(ws, "src/q_learner.py", "class QLearner:\n    def act(self) -> int:\n        return 0\n")
    _write(ws, "src/tictoc_env.py", "def broken(:\n")

    report = orch._run_verification_step(
        {"task_id": "T7", "target_node": "src/q_learner.py", "assigned_agent": "seed_coder"}, include_docs=False
    )

    assert report["status"] == "PASS", report
    assert any("tictoc_env.py" in w and "Outside the task's scope" in w for w in report.get("warnings", []))


def test_writer_task_is_not_judged_on_code(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    ws = orch.workspace_dir
    _write(ws, "core.py", "def broken(:\n")
    _write(ws, "thesis.md", "# Wstęp\nTekst bez wskaźników.\n")

    report = orch._run_verification_step(
        {"task_id": "T15", "target_node": "thesis.md", "assigned_agent": "seed_writer"}, include_docs=True
    )

    assert report["status"] == "PASS", report


def test_cross_role_writes_are_logged(tmp_path: Path) -> None:
    """A tester writing a module is logged (R6). A coder writing a test is skipped outright (N2, 2026-11-15;
    see tests/test_run_1115_fixes.py)."""
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact(
        "test_game.py",
        {"files": [
            {"filename": "test_game.py", "content": "def test_x() -> None:\n    pass\n"},
            {"filename": "game.py", "content": "X = 1\n"},
        ]},
        writer={"agent": "seed_tester", "task_id": "T10"},
    )

    events = json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]
    kinds = {e["type"]: e for e in events}
    assert kinds["CROSS_ROLE_WRITE"]["files"] == ["game.py"]
