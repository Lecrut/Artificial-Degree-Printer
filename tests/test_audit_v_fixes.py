"""Audit V §VI.6/§VI.7 fixes (2026-11-14 run): side artifacts, per-file contract protection, richer exports,
the fixed environment (D1/D2), qualified edit symbols, and derived-artifact repairs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adk.orchestration.building import _plain_symbol
from adk.orchestration.common import MaterializationError, available_package_imports
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.building.import_sync import extract_hyperedge_exports
from adk.tools.building.hypergraph_sync import sync_hypergraph_matrix
from adk.tools.verification.contract_check import check_import_contract
from adk.tools.verification.ref_compiler import compile_symbolic_references


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
    orch.matrix_path = orch.state_dir / "hypergraph_matrix.json"
    shutil.copy2(Path("adk") / "state" / "hypergraph_matrix.json", orch.matrix_path)
    return orch


PLOT = "def generate_diagram_text() -> str:\n    return 'diagram'\n"


def _establish_plot_contract(orch: NeuroSymbolicOrchestrator) -> None:
    orch._materialize_workspace_artifact(
        "plot_results.py",
        {"files": [{"filename": "plot_results.py", "content": PLOT}]},
        establishes_contract=True,
    )


def test_stale_plot_script_attached_to_a_test_repair_is_skipped(tmp_path: Path) -> None:
    """2026-11-14: the tester attached plot_script to every test repair and lost ~95 whole answers over it."""
    orch = _orch(tmp_path)
    _establish_plot_contract(orch)

    orch._materialize_workspace_artifact(
        "test_env.py",
        {
            "test_file": "test_env.py",
            "test_code": "def test_ok() -> None:\n    assert True\n",
            "plot_script": "def something_else() -> None:\n    pass\n",
            "plot_file": "plot_results.py",
        },
    )

    assert (orch.workspace_dir / "test_env.py").exists()
    assert (orch.workspace_dir / "plot_results.py").read_text(encoding="utf-8") == PLOT
    events = {e["type"] for e in json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]}
    assert "SIDE_ARTIFACT_SKIPPED" in events


def test_contract_breach_in_a_non_target_file_restores_it_and_keeps_the_rest(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish_plot_contract(orch)

    orch._materialize_workspace_artifact(
        "test_env.py",
        {
            "files": [
                {"filename": "test_env.py", "content": "def test_ok() -> None:\n    assert True\n"},
                {"filename": "plot_results.py", "content": "def other() -> None:\n    pass\n"},
            ]
        },
    )

    assert (orch.workspace_dir / "test_env.py").exists()
    assert (orch.workspace_dir / "plot_results.py").read_text(encoding="utf-8") == PLOT
    events = {e["type"] for e in json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]}
    assert "CONTRACT_FILE_RESTORED" in events


def test_breach_of_the_target_file_still_raises_and_hands_back_the_removed_source(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish_plot_contract(orch)

    with pytest.raises(MaterializationError, match=r"(?s)generate_diagram_text.*return 'diagram'"):
        orch._materialize_workspace_artifact(
            "plot_results.py",
            {"files": [{"filename": "plot_results.py", "content": "def other() -> None:\n    pass\n"}]},
        )
    assert (orch.workspace_dir / "plot_results.py").read_text(encoding="utf-8") == PLOT


def test_exports_carry_enum_members_and_the_import_path(tmp_path: Path) -> None:
    """2026-11-14: a tester guessed `Player.PLAYER_ONE` and `import synthetic_data_generator` (module in src/)."""
    ws = tmp_path / "ws"
    (ws / "src").mkdir(parents=True)
    (ws / "src" / "__init__.py").write_text("", encoding="utf-8")
    (ws / "src" / "game.py").write_text(
        "from enum import Enum\n\n\nclass Player(Enum):\n    X = 1\n    O = 2\n", encoding="utf-8"
    )
    matrix = tmp_path / "m.json"
    matrix.write_text(json.dumps({"nodes": {}, "edges": {}, "matrix": {}}), encoding="utf-8")
    sync_hypergraph_matrix(ws, matrix)

    exports = extract_hyperedge_exports("ALL", matrix, ws)["exports"]

    assert exports["src/game.py"]["import"] == "src.game"
    assert "Player.X" in exports["src/game.py"]["signatures"]


def test_import_of_a_package_absent_from_the_environment_is_an_l1_finding(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "core.py").write_text("import nonexistent_package_zz9\nimport numpy\nimport json\n", encoding="utf-8")

    violations = check_import_contract(ws, "core.py")

    assert len(violations) == 1 and "nonexistent_package_zz9" in violations[0]


def test_available_packages_lists_canonical_import_lines() -> None:
    packages = available_package_imports()
    assert packages["np"] == "import numpy as np"
    assert "pytest" in packages


def test_symbols_with_py_inside_and_class_prefix_are_normalized() -> None:
    """2026-11-14: `src/experiment/experiment_runner.py.run_all` and `class Player` were rejected."""
    assert _plain_symbol("src/experiment/experiment_runner.py.run_all") == ("run_all", "src/experiment/experiment_runner.py")
    assert _plain_symbol("class Player") == ("Player", None)
    assert _plain_symbol("def main") == ("main", None)


def test_unresolved_pointer_hint_names_the_closest_real_target(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "config.py").write_text("class SignalConfig:\n    pass\n", encoding="utf-8")
    (ws / "thesis.md").write_text(
        "# Praca\nZob. \\ref_ast{generator.py:SignalConfig} i \\ref_ast{file:symbol}.\n", encoding="utf-8"
    )

    res = compile_symbolic_references(ws / "thesis.md", ws, write_compiled=False)

    assert any("config.py:SignalConfig" in e for e in res["errors"])
    assert any("placeholder" in e for e in res["errors"])


def test_fast_repair_of_a_derived_artifact_goes_to_its_producer(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    matrix = {
        "nodes": {
            "n1": {"path": "plot_results.py", "degree": 1, "weight": 1.0, "kind": "authored"},
            "n2": {"path": "figures/comparison.pdf", "degree": 1, "weight": 1.0, "kind": "derived", "producer": "n1"},
        },
        "edges": {"E1": ["n1", "n2"]},
        "matrix": {"n1": {"E1": 1}, "n2": {"E1": 1}},
        "edge_meta": {"E1": {"dynamic": True, "kind": "produces", "producer": "n1"}},
    }
    orch.matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    assert orch._repair_target("figures/comparison.pdf") == "plot_results.py"


def test_pointer_naming_a_directory_is_a_finding_not_a_crash(tmp_path: Path) -> None:
    r"""2026-11-15: `\ref_ast{src:evaluation.py:f}` named the directory `src`; reading it raised PermissionError
    and crashed the run. A wrong pointer is a finding with the corrected form."""
    ws = tmp_path / "ws"
    (ws / "src").mkdir(parents=True)
    (ws / "src" / "evaluation.py").write_text("def evaluate_agent() -> None:\n    pass\n", encoding="utf-8")
    (ws / "thesis.md").write_text(r"Zob. \ref_ast{src:evaluation.py:evaluate_agent}." + "\n", encoding="utf-8")

    res = compile_symbolic_references(ws / "thesis.md", ws, write_compiled=False)

    assert res["status"] == "FAIL"
    assert any("src/evaluation.py:evaluate_agent" in e for e in res["errors"])


def test_failed_publishing_of_one_task_does_not_end_the_suite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    from adk.benchmarks import run_benchmark_suite, runner

    monkeypatch.setattr(runner, "publish_workspace_thesis_bundle", MagicMock(side_effect=PermissionError("katalog")))
    res = run_benchmark_suite(task_keys=["2"], provider="mock", output_root=tmp_path / "out")

    assert "PermissionError" in res["tasks"][0]["artifacts"]["publish_error"]
    assert (tmp_path / "out" / "benchmark_summary.json").exists()
