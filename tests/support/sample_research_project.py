"""A small research project (config, data generator, experiment) as a valid plan, with its interfaces and the rules that judge it."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph import build_from_plan

_CONFIG = '"""Config."""\nCHANNELS: list[str] = ["EEG", "ECG"]\nN_REPETITIONS: int = 3\nSEEDS: list[int] = [0, 1, 2]\n'


_GENERATOR = (
    '"""Generator."""\nfrom src.config import CHANNELS\n\n\n'
    "def generate_sample(channel: str, seed: int) -> list[float]:\n"
    '    """One sample."""\n    pass\n'
)


_EXPERIMENT_IFACE = (
    '"""Entrypoint: writes the f1 row."""\nfrom src.config import CHANNELS, N_REPETITIONS, SEEDS\n'
    "from src.data_generator import generate_sample\n\n\n"
    "def run_experiment() -> list[dict]:\n"
    '    """Run everything."""\n    pass\n'
)


_GOOD = {"src/config.py": _CONFIG, "src/data_generator.py": _GENERATOR, "src/experiment.py": _EXPERIMENT_IFACE}


_ENTRY = "src/experiment.py:run_experiment"


def _rules(violations) -> set[str]:
    return {v.rule for v in violations}


def _h():
    tasks = [
        {"task_id": "T1", "target_node": "tests/test_data_generator.py", "description": "tests", "assigned_agent": "seed_tester"},
        {"task_id": "T2", "target_node": "docs/literature_review.md", "description": "survey", "assigned_agent": "background_researcher"},
    ]
    chapters = [{"index": 1, "title": "Wstęp", "focus": "cel"}, {"index": 4, "title": "Wyniki", "focus": "eksperyment"}]
    return build_from_plan(_GOOD, _ENTRY, tasks, chapters, ["f1"])


def _spec_orch(tmp_path: Path):
    from tests.support.orchestrator_sandbox import _orch

    orch = _orch(tmp_path)
    orch.include_docs = False
    orch._build_project_hypergraph(_GOOD, {"entrypoint": _ENTRY}, [])
    return orch
