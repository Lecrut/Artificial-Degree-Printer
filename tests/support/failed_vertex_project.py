"""A planned project with the hypergraph of a run in which a vertex fails: the tasks, the events and the states a re-plan test starts from."""

from __future__ import annotations

import json
from pathlib import Path

from adk.mocks import code_fixtures as fx
from adk.orchestration.common import _RunState
from tests.support.orchestrator_sandbox import _orch
from tests.support.planned_projects import SPEC, with_plan

_TASKS = [
    {"task_id": "T1", "target_node": "config.py", "description": "Configuration", "assigned_agent": "seed_coder"},
    {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"},
    {"task_id": "T3", "target_node": "tests/test_core.py", "description": "Tests of core.py", "assigned_agent": "seed_tester"},
]


def _planned(tmp_path: Path):
    orch = _orch(tmp_path)
    h = with_plan(orch, SPEC["interfaces"], SPEC["entrypoint"], _TASKS, [{"index": 1, "title": "Wstęp", "focus": "cel"}])
    return orch, h


def _events(orch, seen: int) -> list[dict]:
    lines = orch.logger.events_path.read_text(encoding="utf-8").splitlines() if orch.logger.events_path.exists() else []
    return [json.loads(line) for line in lines[seen:]]


def _seen(orch) -> int:
    return len(orch.logger.events_path.read_text(encoding="utf-8").splitlines()) if orch.logger.events_path.exists() else 0


_CONFIG = 'import os\n\n\nclass Paths:\n    def results(self) -> str:\n        """Dir."""\n        return os.getcwd()\n\n\ndef get_results_dir() -> str:\n    """Dir."""\n    return self.output_path\n'


def _repair_once(tmp_path: Path, failures: int, issue: str | None = None) -> tuple[dict, str]:
    from adk.orchestration import repair

    orch, h = _planned(tmp_path)
    core = fx.TICTACTOE_CORE_CODE
    (orch.workspace_dir / "core.py").write_text(core, encoding="utf-8")
    line = next(i for i, text in enumerate(core.splitlines(), 1) if text.startswith("def check_winner("))
    h.vertices["core.py"].failures = failures
    built: list[tuple[dict, str]] = []
    orch._execute_builder_step = lambda task, model_tier="SML", **_k: built.append((task, model_tier))
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda *_a, **_k: False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder",
               "issues": [issue or f"Ruff lint failure: core.py:{line + 2}:5: F821 Undefined name `x`"], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"}
    state = _RunState(user_prompt="p", max_retries=repair.FAST_REPAIR_ATTEMPTS, multi_cycle_waves=True, tasks=[task])
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    return built[0]
