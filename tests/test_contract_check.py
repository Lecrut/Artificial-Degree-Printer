from __future__ import annotations

from pathlib import Path

from adk.hypergraph import build_from_plan, diff, observe

_CORE = '"""Core."""\n\n\ndef get_board(moves: list) -> list:\n    """Board."""\n\n\ndef check_winner(board: list) -> str:\n    """Winner."""\n'
_CONFIG = '"""Config."""\nALPHA: float = 0.1\n'


def _h_and_workspace(tmp_path: Path, files: dict[str, str]):
    interfaces = {"config.py": _CONFIG, "core.py": "from config import ALPHA\n" + _CORE}
    tasks = [{"task_id": "T1", "target_node": "tests/test_core.py", "description": "tests", "assigned_agent": "seed_tester"}]
    h, _ = build_from_plan(interfaces, None, tasks, [], [])
    for rel, body in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(body, encoding="utf-8")
    return h


def test_a_test_using_names_the_interface_lacks_is_a_violation(tmp_path: Path):
    """The test <-> module contract now lives in H: `from core import get_winner` and `core.is_terminal(...)` are
    both uses of names `core.py`'s interface does not declare (the old matrix check, Audit VIII C1)."""
    h = _h_and_workspace(
        tmp_path,
        {
            "core.py": "from config import ALPHA\n" + _CORE.replace('"""Board."""', '"""Board."""\n    return []'),
            "config.py": _CONFIG,
            "tests/test_core.py": (
                "import core\nfrom core import get_board, get_winner\n\n"
                "def test_x():\n    assert core.is_terminal(get_board([]))\n"
            ),
        },
    )
    found = [v for v in diff(h, observe(tmp_path)) if v.rule == "IMPORT_OUTSIDE_SPEC"]
    assert len(found) == 1 and found[0].culprit == "tests/test_core.py"
    assert "get_winner" in found[0].detail and "is_terminal" in found[0].detail


def test_declared_names_used_any_way_are_no_violation(tmp_path: Path):
    h = _h_and_workspace(
        tmp_path,
        {
            "config.py": _CONFIG,
            "core.py": "from config import ALPHA\n" + _CORE,
            "tests/test_core.py": (
                "import core as c\nfrom core import get_board\n\n"
                "def test_x(monkeypatch):\n"
                "    c.EXTRA = 5\n"  # a store, not a use
                "    assert c.check_winner(get_board([])) is not None\n"
            ),
        },
    )
    assert [v for v in diff(h, observe(tmp_path)) if v.culprit == "tests/test_core.py"] == []


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
