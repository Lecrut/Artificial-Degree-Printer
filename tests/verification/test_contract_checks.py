"""Contract checks of code against the specification: a test may use only names the interface declares, an entrypoint reads config and has no numeric defaults, stubs keep their signatures, a package missing from the environment is a finding."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph import build_from_plan, diff, observe, spec_from_stub
from adk.hypergraph.oracles import validate_test_on_stubs
from adk.orchestration.common import available_package_imports
from adk.tools.verification.contract_check import check_import_contract, stub_source
from tests.support.sample_research_project import _ENTRY, _GOOD
from tests.support.skeleton_agent import SKELETON_AGENT
from tests.support.tictactoe_interface import ENV_INTERFACE
from tests.support.workspace_files import _write

_BASELINE = (
    '"""Z-score baseline."""\n\n\nclass ZScoreBaseline:\n'
    '    """Detector."""\n    threshold: float\n\n'
    "    def __init__(self, threshold: float = 3.0) -> None:\n"
    '        """Create."""\n        self.threshold = threshold\n\n'
    "    def score(self, x: float) -> float:\n"
    '        """Absolute score: never negative."""\n'
    "        return abs(x)\n"
)


_SPEC_IFACES = {"src/baseline.py": _BASELINE, "src/experiment.py": '"""E."""\n\n\ndef run_experiment() -> int:\n    """Run."""\n    return 0\n'}


def _baseline_h(tmp_path: Path):
    h, problems = build_from_plan(
        _SPEC_IFACES, "src/experiment.py:run_experiment",
        [{"task_id": "T1", "target_node": "tests/test_baseline.py", "description": "t", "assigned_agent": "seed_tester"}], [], [],
    )
    assert problems == []
    ws = tmp_path / "ws"
    for rel, source in _SPEC_IFACES.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(source, encoding="utf-8")
    (ws / "tests").mkdir()
    return h, ws


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


def test_specification_carries_enum_members_and_the_import_path() -> None:
    """2026-11-14: a tester guessed `Player.PLAYER_ONE` and `import synthetic_data_generator` (module in src/)."""
    spec = spec_from_stub("src/game.py", "from enum import Enum\n\n\nclass Player(Enum):\n    X = 1\n    O = 2\n", {})
    assert spec["import"] == "src.game"
    assert "Player.X" in spec["symbols"]


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


def test_tests_may_read_only_declared_attributes(tmp_path: Path):
    """T1, 02 T10: `hasattr(model, 'mean_')` — an attribute the interface declared nowhere."""
    h, ws = _baseline_h(tmp_path)
    assert h.edges["I:src/baseline.py"].spec["symbols"]["ZScoreBaseline.threshold"] == {"kind": "attr"}
    (ws / "tests/test_baseline.py").write_text(
        "from src.baseline import ZScoreBaseline\n\n\ndef test_fit():\n    m = ZScoreBaseline(3.0)\n"
        "    assert m.threshold == 3.0\n    assert hasattr(m, 'mean_')\n",
        encoding="utf-8",
    )
    found = [v for v in diff(h, observe(ws)) if v.rule == "TEST_OUTSIDE_SPEC"]
    assert len(found) == 1 and "ZScoreBaseline.mean_" in found[0].detail and "threshold" not in found[0].detail


def test_a_test_is_validated_on_the_stubs_before_any_implementation(tmp_path: Path):
    """T1, 02 T11: `np` without import; T9: a wrong import path — both found on the stubs."""
    h, ws = _baseline_h(tmp_path)
    good = ws / "tests/test_baseline.py"
    good.write_text("from src.baseline import ZScoreBaseline\n\n\ndef test_score():\n    assert ZScoreBaseline().score(-2.0) == 2.0\n", encoding="utf-8")
    assert validate_test_on_stubs(ws, "tests/test_baseline.py", h) == []
    good.write_text(
        "from src.baseline import ZScoreBaseline\n\n\ndef test_score():\n    x = np.array([1.0])\n    assert ZScoreBaseline().score(x[0]) == 1.0\n",
        encoding="utf-8",
    )
    bad = validate_test_on_stubs(ws, "tests/test_baseline.py", h)
    assert bad and bad[0].rule == "TEST_INVALID_ON_STUBS" and "NameError" in bad[0].detail
    good.write_text("from baseline import ZScoreBaseline\n\n\ndef test_score():\n    assert ZScoreBaseline().score(1.0) == 1.0\n", encoding="utf-8")
    assert validate_test_on_stubs(ws, "tests/test_baseline.py", h)[0].rule == "TEST_INVALID_ON_STUBS"


def test_stub_keeps_attributes_declared_by_self_assignment(tmp_path: Path):
    """02: `self.threshold = threshold` vanished with the body of __init__; the spec gate rejected the harness's own
    stubs and the run crashed before its first task."""
    baseline = (
        '"""Baseline."""\n\n\nclass ZScoreBaseline:\n    """Detector."""\n\n'
        "    def __init__(self, threshold: float = 3.0) -> None:\n"
        '        """Store the threshold."""\n        self.threshold: float = threshold\n        self.fitted = False\n\n'
        "    def detect(self, x: list) -> list:\n        \"\"\"Flags.\"\"\"\n        pass\n"
    )
    stub = stub_source(baseline)
    assert "threshold: 'float'" in stub and "fitted: 'object'" in stub and "raise NotImplementedError" in stub
    interfaces = {**_GOOD, "src/baseline.py": baseline}
    experiment = _GOOD["src/experiment.py"].replace(
        "from src.data_generator import generate_sample\n",
        "from src.data_generator import generate_sample\nfrom src.baseline import ZScoreBaseline\n",
    )
    interfaces["src/experiment.py"] = experiment
    h, problems = build_from_plan(interfaces, _ENTRY, [], [], [])
    assert problems == []
    for rel, src in interfaces.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(stub_source(src), encoding="utf-8")
    assert diff(h, observe(tmp_path)) == []


def test_a_stub_finding_names_the_functions() -> None:
    """01 game_env: "a function still only raises NotImplementedError" three times, never which one."""
    from adk.hypergraph.oracles import stub_functions

    source = "class Env:\n    def reset(self):\n        raise NotImplementedError\n    def step(self):\n        return 1\n\ndef helper():\n    ...\n"
    assert sorted(stub_functions(source)) == ["Env.reset", "helper"]


def test_a_test_may_read_what_a_function_returns() -> None:
    """02: `mask = get_ground_truth_mask(...); mask.shape` rejected the tester four times as undeclared API."""
    from types import SimpleNamespace

    from adk.hypergraph.observe import _test_diff

    symbols = {"get_ground_truth_mask": {"kind": "func"}, "Model": {"kind": "class"}}
    h = SimpleNamespace(edges={"I:gen.py": SimpleNamespace(spec={"symbols": symbols})})
    seen = {"attrs_used": [("gen.py", "get_ground_truth_mask", "shape"), ("gen.py", "Model", "secret")]}
    found = _test_diff("tests/test_gen.py", seen, h)
    assert len(found) == 1 and "Model.secret" in found[0].detail and "shape" not in found[0].detail


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


def test_static_import_contract_catches_a_wrong_name_without_running_anything(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    _write(ws, "src/__init__.py", "")
    _write(ws, "src/game.py", "class TicTacToeGame:\n    pass\n")
    _write(ws, "src/env.py", "from .game import TicTacToe\nfrom src.game import TicTacToeGame\n")

    violations = check_import_contract(ws, "src/env.py")

    assert len(violations) == 1
    assert "TicTacToe " in violations[0] + " " and "TicTacToeGame" in violations[0]


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


def test_specification_carries_class_method_signatures() -> None:
    """What a tester sees of a module is its σ in H: every method with its parameters (2026-11-12: guessed APIs)."""
    symbols = spec_from_stub("agent.py", SKELETON_AGENT, {})["symbols"]

    assert symbols["Agent.__init__"]["params"] == ["self", "alpha"]
    assert symbols["Agent.act"] == {"kind": "method", "params": ["self", "state"], "required": ["state"]}
