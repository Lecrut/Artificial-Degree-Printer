"""A small game project (a module and its user) planned with an interface a test may amend."""

from __future__ import annotations

from pathlib import Path

from tests.support.orchestrator_sandbox import _orch
from tests.support.planned_projects import with_plan

_CONFIG = '"""Config."""\nSEED: int = 1\n'


_GAME = (
    '"""Game."""\nfrom config import SEED\n\n\n'
    "def play(seed: int) -> int:\n"
    '    """Score of one game: never negative."""\n'
)


_RUN = '"""Run."""\nfrom game import play\n\n\ndef main() -> None:\n    """Run the experiment."""\n'


_GAME_IMPL = _GAME + "    return seed % 3\n"


def _planned(tmp_path: Path, chapters: list[dict] | None = None):
    orch = _orch(tmp_path)
    tasks = [{"task_id": "T3", "target_node": "tests/test_game.py", "description": "tests", "assigned_agent": "seed_tester"}]
    h = with_plan(orch, {"config.py": _CONFIG, "game.py": _GAME, "run.py": _RUN}, "run.py:main", tasks, chapters)
    for rel, src in (("config.py", _CONFIG), ("game.py", _GAME_IMPL), ("run.py", _RUN.replace('"""Run the experiment."""', '"""Run the experiment."""\n    play(0)'))):
        (orch.workspace_dir / rel).write_text(src, encoding="utf-8")
    return orch, h


_MISMATCH = "API_SIGNATURE [game.py]: play(seed) takes a different parameter than the interface plans"


def _with_repeated_breach(orch) -> None:
    orch._remember_verdict("game.py", "T2", [_MISMATCH])
    orch._remember_verdict("game.py", "T2_FIX1", [_MISMATCH])


def _planner_answers(orch, answer: dict) -> list[dict]:
    seen: list[dict] = []

    def agent(md, payload, **_kw):
        assert Path(md).name == "plan_change_guard.md"
        seen.append(payload)
        return {"status": "ok", "output": answer}

    orch._call_agent = agent
    return seen
