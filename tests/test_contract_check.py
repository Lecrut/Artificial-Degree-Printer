from __future__ import annotations

import json
from pathlib import Path

from adk.tools.verification import check_test_contract


def _setup(tmp_path: Path, files: dict[str, str], edges: dict[str, list[str]]) -> tuple[Path, Path]:
    ws = tmp_path / "workspace"
    ws.mkdir()
    for name, content in files.items():
        (ws / name).write_text(content, encoding="utf-8")
    nodes = {
        "v1": {"path": "config.py"},
        "v2": {"path": "core.py"},
        "v5": {"path": "test_core.py"},
        "v7": {"path": "test_other.py"},
    }
    matrix_file = tmp_path / "hypergraph_matrix.json"
    matrix_file.write_text(json.dumps({"nodes": nodes, "edges": edges, "matrix": {}}), encoding="utf-8")
    return ws, matrix_file


def test_contract_reports_symbols_missing_from_coupled_module(tmp_path: Path):
    ws, matrix_file = _setup(
        tmp_path,
        {
            "core.py": "def get_board(moves):\n    return []\n\ndef check_winner(board):\n    return ''\n",
            "test_core.py": (
                "import core\nfrom core import get_board, get_winner\n\n"
                "def test_x():\n    assert core.is_terminal(get_board([]))\n"
            ),
        },
        {"E4": ["v2", "v5"]},
    )

    violations = check_test_contract(ws, matrix_file)

    assert len(violations) == 1
    assert "core.get_winner" in violations[0] and "core.is_terminal" in violations[0]
    assert "check_winner" in violations[0] and "get_board" in violations[0]


def test_contract_has_no_false_positives(tmp_path: Path):
    ws, matrix_file = _setup(
        tmp_path,
        {
            "config.py": "ALPHA = 0.1\n",
            "core.py": (
                "from config import ALPHA\n"
                "try:\n    import numpy as np\n    HAS_NP = True\nexcept ImportError:\n    HAS_NP = False\n"
                "SIZE: int = 3\n"
                "class Game:\n    def play(self):\n        return 1\n"
            ),
            "test_core.py": (
                "import core as c\nfrom core import Game\n\n"
                "def test_x(monkeypatch):\n"
                "    c.EXTRA = 5\n"
                "    assert c.ALPHA and c.SIZE and c.HAS_NP in (True, False)\n"
                "    assert Game().play() == 1\n"
            ),
            # Not coupled by any hyperedge -> ignored even though it is wrong.
            "test_other.py": "import core\n\ndef test_y():\n    core.nope()\n",
        },
        {"E1": ["v1", "v2"], "E4": ["v2", "v5"]},
    )

    assert check_test_contract(ws, matrix_file) == []


def test_contract_skips_dynamic_modules(tmp_path: Path):
    ws, matrix_file = _setup(
        tmp_path,
        {
            "core.py": "def __getattr__(name):\n    return 1\n",
            "test_core.py": "import core\n\ndef test_x():\n    assert core.anything\n",
        },
        {"E4": ["v2", "v5"]},
    )

    assert check_test_contract(ws, matrix_file) == []


def test_entrypoint_numeric_defaults_are_a_contract_violation(tmp_path: Path):
    from adk.tools.verification import check_entrypoint_parameters

    (tmp_path / "core.py").write_text(
        "def train_and_evaluate(out='results.csv', n_runs: int = 50, seed: int = 42, verbose=False):\n    pass\n",
        encoding="utf-8",
    )
    violations = check_entrypoint_parameters(tmp_path, "core.py:train_and_evaluate")
    assert len(violations) == 1
    assert "n_runs=50" in violations[0] and "seed=42" in violations[0]
    assert "verbose" not in violations[0]


def test_entrypoint_reading_config_symbols_passes(tmp_path: Path):
    from adk.tools.verification import check_entrypoint_parameters

    (tmp_path / "core.py").write_text(
        "import config\n\ndef main(seed: int = config.SEED):\n    pass\n", encoding="utf-8"
    )
    assert check_entrypoint_parameters(tmp_path, "core.py:main") == []


def test_closure_warns_about_declared_but_unused_parameters(tmp_path: Path):
    from adk.tools.verification import check_parameter_closure

    (tmp_path / "config.py").write_text("SEED = 1\nUNUSED_KNOB = 3\n", encoding="utf-8")
    (tmp_path / "core.py").write_text("import config\nprint(config.SEED)\n", encoding="utf-8")
    warnings = check_parameter_closure(tmp_path)
    assert any("UNUSED_KNOB" in w for w in warnings)
    assert not any(":SEED" in w for w in warnings)
