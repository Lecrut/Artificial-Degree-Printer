"""§XII R2–R4 (benchmark 2026-11-19): answers rejected for nothing the model could fix, and a crash."""

from __future__ import annotations

from pathlib import Path

import pytest

from adk.orchestration.common import MaterializationError
from adk.tools.evolution import sandbox_verifier
from adk.tools.verification.ref_compiler import compile_symbolic_references
from tests.test_write_gate import _orch

CONFIG = 'LEARNING_RATE: float = 0.1\nSEED: int = 42\n__all__ = ["LEARNING_RATE"]\n'


def _errors(ws: Path, thesis: str) -> list[str]:
    (ws / "thesis.md").write_text(thesis, encoding="utf-8")
    return compile_symbolic_references(ws / "thesis.md", ws, write_compiled=False)["errors"]


def test_writer_is_told_there_are_no_results_yet_instead_of_choosing_from_an_empty_list(tmp_path: Path) -> None:
    """R2: 01 wrote chapters 1–3 before the experiment; 12x "CSV file 'ttt_results' does not exist" after a hint to
    pick a target from `available_csv_columns`, which was empty."""
    errors = _errors(tmp_path, "Wyniki \\ref_csv{ttt_results:mean_reward} i \\ref_csv{ttt_results:n_runs}, \\ref_csv{x}.\n")
    assert len(errors) == 1
    assert "No results exist yet" in errors[0] and "Remove every \\ref_csv" in errors[0]
    assert "available_csv_columns" not in errors[0]


def test_writer_is_pointed_at_results_csv_when_results_exist(tmp_path: Path) -> None:
    (tmp_path / "results.csv").write_text("method,metric,value\nq,win_rate,0.9\n", encoding="utf-8")
    errors = _errors(tmp_path, "Wynik \\ref_csv{ttt_results:win_rate}.\n")
    assert errors == [
        "\\ref_csv{ttt_results:win_rate}: no such file. The results are in results.csv: write "
        "\\ref_csv{results.csv:win_rate} with a column from 'available_csv_columns'."
    ]


def test_files_as_a_path_to_content_mapping_is_saved(tmp_path: Path) -> None:
    """R3: 01 R1_2_FIX2 "the fields ['files'] match no allowed shape" for an otherwise clear answer."""
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact("config.py", {"files": {"config.py": CONFIG}})
    assert (orch.workspace_dir / "config.py").read_text(encoding="utf-8") == CONFIG


def test_one_edit_of_several_existing_symbols_is_applied_symbol_by_symbol(tmp_path: Path) -> None:
    """R3: 01 T3_FIX1 sent `__all__` together with the module's constants and lost a repair attempt."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "config.py").write_text(CONFIG, encoding="utf-8")
    code = 'LEARNING_RATE: float = 0.2\nSEED: int = 7\n__all__ = ["LEARNING_RATE", "SEED"]\n'
    orch._materialize_workspace_artifact("config.py", {"ast_edits": [{"symbol": "__all__", "code": code}]})
    text = (orch.workspace_dir / "config.py").read_text(encoding="utf-8")
    assert "LEARNING_RATE: float = 0.2" in text and "SEED: int = 7" in text and "__all__ = ['LEARNING_RATE', 'SEED']" in text


def test_a_new_name_is_still_not_added_in_passing(tmp_path: Path) -> None:
    """Audit VI X3 stays: an edit cannot slip an unplanned name into the module next to the one it targets."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "config.py").write_text(CONFIG, encoding="utf-8")
    code = 'SEED: int = 7\nNEW_THING: int = 1\n'
    with pytest.raises(MaterializationError, match="also contains NEW_THING"):
        orch._materialize_workspace_artifact("config.py", {"ast_edits": [{"symbol": "SEED", "code": code}]})


def test_a_hanging_validator_candidate_is_rejected_not_a_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R4: 2026-11-19 `citation_bib_validator.py` timed out on its sample and the TimeoutExpired ended run 01."""
    monkeypatch.setattr(sandbox_verifier, "SAMPLE_TIMEOUT_S", 1)
    result = sandbox_verifier.evaluate_and_promote_validator(
        "slow_validator", "import time\ntime.sleep(5)\n", "bad", "good",
        verification_dir=tmp_path / "verification", evolution_history_path=tmp_path / "history.json",
    )
    assert result["status"] == "REJECTED" and "did not finish" in result["reason"]
    assert not (tmp_path / "verification" / "slow_validator.py").exists()
