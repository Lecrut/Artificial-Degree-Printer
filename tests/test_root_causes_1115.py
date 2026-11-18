"""Root causes of the 2026-11-15 run of benchmark 01 (audit §VI.12: U1-U10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adk.orchestration.plan_interfaces import _interface_gaps, _plan_interfaces
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.verification.contract_check import stub_source


def _orch(tmp_path: Path) -> NeuroSymbolicOrchestrator:
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


ENV_INTERFACE = '''"""Game environment."""
BOARD_SIZE: int = 9


class TicTacToeEnv:
    """Board and rules."""

    def __init__(self, seed: int) -> None:
        """Create an empty board."""
        self.board = [0] * BOARD_SIZE

    def step(self, action: int) -> tuple[list[int], float, bool]:
        """Return (board, reward, done)."""
        return self.board, 0.0, False
'''


def test_stub_source_keeps_the_interface_and_drops_every_body() -> None:
    """U2: the model's "skeleton" had 0 NotImplementedError bodies and 9 half implementations."""
    stub = stub_source(ENV_INTERFACE + "\nprint('side effect')\n")
    assert stub is not None
    assert "BOARD_SIZE: int = 9" in stub
    assert "def step(self, action: int) -> tuple[list[int], float, bool]:" in stub
    assert '"""Return (board, reward, done)."""' in stub
    assert stub.count("raise NotImplementedError") == 2
    assert "self.board" not in stub and "print(" not in stub
    assert stub_source("def broken(:\n") is None


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


def test_interface_gaps_name_missing_modules_and_unknown_names_only() -> None:
    """U1: tasks named TicTacToeEnv.get_state_hash, the contract had no such method."""
    tasks = [
        {"description": "Implementacja `TicTacToeEnv.step()` i get_state_hash() w src/env.py", "target_node": "src/env.py"},
        {"description": "Agent Q-Learning w src/agent.py, np.argmax(q) i `config.py`", "target_node": "src/agent.py"},
        {"description": "Testy TicTacToeEnv.step() w tests/test_env.py", "target_node": "tests/test_env.py"},
    ]
    gaps = _interface_gaps(tasks, {"src/env.py": ENV_INTERFACE})
    assert any("src/agent.py" in g for g in gaps)
    names = next(g for g in gaps if "names" in g)
    assert "get_state_hash" in names
    assert "argmax" not in names and "step" not in names and "py" not in names.split(": ")[1]
    assert _interface_gaps([{"description": "Rozdział 1", "target_node": "thesis.md"}], {}) == []


def test_a_new_test_file_sees_the_signatures_of_every_code_module(tmp_path: Path) -> None:
    """U3: exports came from import edges, so a new test saw only plot_results.py (T7, T10)."""
    from tests._plans import with_plan

    orch = _orch(tmp_path)
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "env.py").write_text(ENV_INTERFACE, encoding="utf-8")
    tasks = [{"task_id": "T7", "target_node": "tests/test_env.py", "description": "tests", "assigned_agent": "seed_tester"}]
    with_plan(orch, {"src/env.py": ENV_INTERFACE}, None, tasks)
    seen: dict[str, Any] = {}

    def _capture(_md: Any, payload: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        seen.update(payload)
        return {"status": "ok", "output": {"test_file": "tests/test_env.py", "test_code": "def test_x() -> None:\n    assert True\n"}}

    orch._call_agent = _capture
    orch._execute_builder_step({"task_id": "T7", "target_node": "tests/test_env.py", "assigned_agent": "seed_tester"}, "SML")
    # The test of src/env.py sees that module's σ from H (its I bag), nothing of the rest of the project.
    assert "TicTacToeEnv.step" in seen["specification"]["src/env.py"]["symbols"]
    assert "exports" not in seen and "grounded_hypergraph_state" not in seen
    assert any("tests/" in item for item in seen["done_when"])


def test_ruff_concise_and_pytest_short_traceback_paths_are_located(tmp_path: Path) -> None:
    """U8: `path.py:172:33: F821` was "unlocated" and the repair went to the core module."""
    orch = _orch(tmp_path)
    for rel in ("src/game_environment.py", "tests/test_env.py"):
        (orch.workspace_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (orch.workspace_dir / rel).write_text("X = 1\n", encoding="utf-8")
        orch._resolve_target_node(rel)
    ruff = "Ruff lint failure: adk\\workspace\\benchmarks\\_evolved_adk_state\\01\\workspace\\src\\game_environment.py:172:33: F821 Undefined name `idx`"
    assert orch._workspace_paths_in(ruff) == ["src/game_environment.py"]
    trace = "tests/test_env.py:17: in test_run\n    with patch('src.x')\nC:\\Python\\Lib\\unittest\\mock.py:1497: in __enter__"
    assert orch._workspace_paths_in(trace) == ["tests/test_env.py"]


def test_plan_never_targets_results_and_puts_tests_in_tests_dir(tmp_path: Path) -> None:
    """U4, U5: T16 on results.csv went to the tester; test_experiment.py appeared at the workspace root."""
    orch = _orch(tmp_path)
    orch.blueprint_path.write_text(json.dumps({"entrypoint": "src/experiment.py:run"}), encoding="utf-8")
    agents = {"coder": "seed_coder", "tester": "seed_tester", "writer": "seed_writer"}
    results = orch._clean_task({"task_id": "T16", "description": "Wyniki", "target_node": "results.csv", "assigned_agent": "seed_tester"}, 0, agents)
    assert (results["target_node"], results["assigned_agent"]) == ("src/experiment.py", "seed_coder")
    test = orch._clean_task({"task_id": "T4", "description": "Testy", "target_node": "test_experiment.py", "assigned_agent": "seed_tester"}, 1, agents)
    assert test["target_node"] == "tests/test_experiment.py"


def test_results_pointer_findings_wait_for_green_code_and_refs_join_the_critic(tmp_path: Path) -> None:
    """U9: Q1-Q4 each gave the writer CRITIC + REFS on \\ref_csv while results.csv did not exist."""
    orch = _orch(tmp_path)
    red = orch._tasks_from_audit(
        {
            "pytest_status": "FAIL",
            "pytest_errors": ["pytest nie przechodzi"],
            "symbolic_errors": ["CSV file 'results.csv' does not exist", "Malformed tag \\ref_ast{Agent.move}"],
            "trigger_issues": ["Unresolved pointer: \\ref_csv{results.csv}"],
        },
        1,
    )
    ids = [t["task_id"] for t in red]
    assert not any(i.endswith("_REFS") for i in ids)
    critic = next(t for t in red if t["task_id"].endswith("_CRITIC"))
    assert "ref_ast{Agent.move}" in critic["description"] and "ref_csv" not in critic["description"]

    green = orch._tasks_from_audit(
        {"pytest_status": "PASS", "csv_columns": ["method"], "symbolic_errors": ["CSV row 'x' does not exist"], "trigger_issues": ["Teza bez liczby."]},
        2,
    )
    assert [t["task_id"] for t in green] == ["Q2_CRITIC"]
    assert "[K1]" in green[0]["description"] and "[K2]" in green[0]["description"]


def test_writer_sees_the_whole_target_chapter_or_the_chapters_with_the_named_pointers() -> None:
    """A chapter was cut to 1500 characters before "replace the section"; CRITIC tasks saw only the last 600."""
    from adk.orchestration.building import _document_context

    ch1 = "## Rozdział 1: Wstęp\n" + "a" * 3000 + " KONIEC1"
    ch4 = "## Rozdział 4: Wyniki\nWynik \\ref_csv{results.csv} jest dobry. " + "b" * 2000
    doc = f"# Praca\n\n{ch1}\n\n{ch4}\n\n## Rozdział 6: Wnioski\nKoniec pracy.\n"
    whole = _document_context(doc, "Chapter 1: introduction in thesis.md")
    assert "KONIEC1" in whole and "CHAPTER 1" in whole
    critic = _document_context(doc, "Fix thesis.md: [K1] Unresolved pointer: \\ref_csv{results.csv}")
    assert "\\ref_csv{results.csv} jest dobry" in critic and "KONIEC1" not in critic
    assert "LAST 600" in _document_context(doc, "Fix the style of thesis.md")


def test_the_experiment_runs_plot_results_from_src(tmp_path: Path) -> None:
    """src/plot_results.py was never run: the runner looked only at the root and code/."""
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "experiment.py").write_text(
        "from pathlib import Path\n\ndef run() -> None:\n    Path('results.csv').write_text('method,metric,value\\nq,win,1\\n')\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "plot_results.py").write_text(
        "from pathlib import Path\n\ndef generate_plots(output_dir: str = '.') -> list[str]:\n"
        "    Path(output_dir, 'plotted.txt').write_text('ok')\n    return ['plotted.txt']\n",
        encoding="utf-8",
    )
    result = execute_workspace_experiment(tmp_path, entrypoint="src/experiment.py:run")
    assert result["ok"], result["error"]
    assert (tmp_path / "plotted.txt").exists()


def test_an_experiment_error_reaches_the_task_on_the_entrypoint_module(tmp_path: Path) -> None:
    """Since U5 no task targets results.csv, so an experiment error attached only there reached no one."""
    orch = _orch(tmp_path)
    orch.blueprint_path.write_text(json.dumps({"entrypoint": "src/experiment.py:run"}), encoding="utf-8")
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "experiment.py").write_text("def run() -> None:\n    return None\n", encoding="utf-8")
    orch._resolve_target_node("src/experiment.py")
    orch._last_experiment_error = "AttributeError: 'Env' object has no attribute 'get_state_hash'"
    report = orch._run_verification_step({"task_id": "T12", "target_node": "src/experiment.py"})
    assert report["status"] == "FAIL"
    assert any("get_state_hash" in str(i) for i in report["supervisors"]["code_auditor"]["issues"] + report.get("errors", []))
