"""Edits of single symbols: an unknown public name is refused with the names that exist, a definition is not duplicated, imports merge without dropping names in use, a method is replaced inside its class and a new name is never added in passing."""

from __future__ import annotations

from pathlib import Path

import pytest

from adk.orchestration.common import MaterializationError
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.building.ast_editor import (
    declared_names,
    edit_ast_node,
    whole_module_loss,
)
from tests.support.config_module_source import CONFIG
from tests.support.orchestrator_sandbox import _orch
from tests.support.skeleton_agent import SKELETON_AGENT

_EXPERIMENT = (
    '"""Experiment entrypoint."""\n'
    "from src.config import CHANNELS, NOISE_LEVELS, N_REPETITIONS\n"
    "from src.data_types import SignalSample\n\n\n"
    "def run_experiment():\n"
    "    return [CHANNELS, NOISE_LEVELS, N_REPETITIONS]\n"
)


def _establish(orch: NeuroSymbolicOrchestrator) -> None:
    orch._materialize_workspace_artifact("agent.py", {"files": [{"filename": "agent.py", "content": SKELETON_AGENT}]})


def test_unknown_public_symbol_is_refused_with_existing_names(tmp_path: Path):
    """02, 16:53:35: edits of `fit`/`predict` aimed at experiment.py became module functions."""
    path = tmp_path / "src" / "experiment.py"
    path.parent.mkdir()
    path.write_text(_EXPERIMENT, encoding="utf-8")
    planned = declared_names(_EXPERIMENT)  # the plan's interface of experiment.py: only run_experiment
    res = edit_ast_node(path, "fit", "def fit(self, samples):\n    pass\n", planned=planned)
    assert res["status"] == "error" and res["guard"] == "TARGET_NOT_FOUND"
    assert "run_experiment" in res["error"]
    assert path.read_text(encoding="utf-8") == _EXPERIMENT
    # a symbol the plan declares may be added
    assert edit_ast_node(path, "fit", "def fit():\n    pass\n", planned=planned | {"fit"})["action"] == "appended"


def test_snippet_without_target_or_with_extra_definitions_is_refused(tmp_path: Path):
    """02, 17:25:00: symbol `__main__` with three defs appended the last one (`predict`)."""
    path = tmp_path / "experiment.py"
    path.write_text(_EXPERIMENT, encoding="utf-8")
    no_target = edit_ast_node(path, "__main__", "def fit(self):\n    pass\n\ndef predict(self):\n    pass\n")
    assert no_target["guard"] == "TARGET_NOT_IN_CODE"
    extra = edit_ast_node(path, "run_experiment", "def run_experiment():\n    return 1\n\ndef fit(self):\n    pass\n")
    assert extra["guard"] == "EXTRA_DEFINITIONS" and "fit" in extra["error"]
    assert path.read_text(encoding="utf-8") == _EXPERIMENT


def test_duplicate_definition_is_refused(tmp_path: Path):
    """02: three `run_experiment` in experiment.py, edits replaced the first while Python ran the last."""
    path = tmp_path / "experiment.py"
    path.write_text(_EXPERIMENT + "\n\ndef run_experiment():\n    return None\n", encoding="utf-8")
    res = edit_ast_node(path, "run_experiment", "def run_experiment():\n    return 2\n")
    assert res["guard"] == "DUPLICATE_DEFINITION"


def test_import_of_an_already_imported_module_drops_stale_names(tmp_path: Path):
    """02: the stale `from src.config import N_REPETITIONS` could never be removed and was the final ImportError."""
    path = tmp_path / "experiment.py"
    path.write_text(_EXPERIMENT, encoding="utf-8")
    res = edit_ast_node(
        path,
        "run_experiment",
        "from src.config import get_channels\n\ndef run_experiment():\n    return [get_channels(), SignalSample]\n",
    )
    assert res["status"] == "ok"
    source = path.read_text(encoding="utf-8")
    assert source.count("from src.config import") == 1
    assert "get_channels" in source and "N_REPETITIONS" not in source and "CHANNELS," not in source
    assert "from src.data_types import SignalSample" in source  # other modules' imports untouched


def test_used_old_names_survive_the_import_merge(tmp_path: Path):
    path = tmp_path / "mod.py"
    path.write_text("from typing import List\n\n\ndef a() -> List[int]:\n    return []\n\n\ndef b():\n    return 1\n", encoding="utf-8")
    assert edit_ast_node(path, "b", "from typing import Any\n\ndef b() -> Any:\n    return 1\n")["status"] == "ok"
    source = path.read_text(encoding="utf-8")
    assert "List" in source and "Any" in source and source.count("from typing import") == 1


def test_tests_and_private_helpers_may_still_be_added(tmp_path: Path):
    test_file = tmp_path / "tests" / "test_mod.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_a():\n    assert True\n", encoding="utf-8")
    assert edit_ast_node(test_file, "test_b", "def test_b():\n    assert True\n")["status"] == "ok"
    module = tmp_path / "mod.py"
    module.write_text("def a():\n    return 1\n", encoding="utf-8")
    planned = {"a"}
    assert edit_ast_node(module, "_helper", "def _helper():\n    return 2\n", planned=planned)["action"] == "appended"
    assert edit_ast_node(module, "__main__", "if __name__ == '__main__':\n    a()\n", planned=planned)["action"] == "appended"


def test_whole_module_answer_may_not_drop_public_symbols():
    """02, 17:24:51: symbol `src.experiment` with three import lines overwrote the whole file."""
    assert whole_module_loss(_EXPERIMENT, "import numpy as np\nimport pandas as pd\n") == ["run_experiment"]
    assert whole_module_loss(_EXPERIMENT, _EXPERIMENT.replace("return [", "return (")) == []


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


def test_symbol_edit_replaces_one_method_inside_its_class(tmp_path: Path) -> None:
    path = tmp_path / "agent.py"
    path.write_text(SKELETON_AGENT, encoding="utf-8")

    res = edit_ast_node(path, "Agent.act", "def act(self, state: tuple) -> int:\n    return 0\n")

    assert res["status"] == "ok" and res["action"] == "replaced"
    source = path.read_text(encoding="utf-8")
    assert "return 0" in source and source.count("def act") == 1 and "def __init__" in source
    assert edit_ast_node(path, "Missing.act", "def act(self) -> int:\n    return 1\n")["status"] == "error"


def test_rejected_symbol_edit_is_an_error_and_nothing_of_the_answer_is_written(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish(orch)

    with pytest.raises(MaterializationError, match="Symbol edits rejected"):
        orch._materialize_workspace_artifact(
            "agent.py",
            {
                "files": [{"filename": "helper.py", "content": "VALUE = 1\n"}],
                "ast_edits": [{"symbol": "Agent.act", "file": "agent.py", "code": "def act(self, state:\n"}],
            },
        )

    assert not (orch.workspace_dir / "helper.py").exists()
    assert (orch.workspace_dir / "agent.py").read_text(encoding="utf-8") == SKELETON_AGENT
