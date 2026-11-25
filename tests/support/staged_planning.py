"""A small planned project (two modules, an experiment, figures) and the planning agents answering it stage by stage, with the overrides a test needs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from adk.mocks.staged import sketch_of, staged_answer
from adk.orchestrator import NeuroSymbolicOrchestrator


def _make_orch(tmp_path: Path) -> NeuroSymbolicOrchestrator:
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


_MOD_A = 'def helper_a() -> int:\n    """Return 1."""\n    return 1\n'


_MOD_B = 'from src.mod_a import helper_a\n\n\ndef helper_b() -> int:\n    """Return 2."""\n    return 2\n'


_EXP = (
    "from src.mod_a import helper_a\n"
    "from src.mod_b import helper_b\n\n"
    'def run_experiment() -> int:\n    """Run; writes score and time."""\n    return helper_a() + helper_b()\n'
)


_PLOTS = 'def plots() -> None:\n    """Figures."""\n'


_ENTRY = "src/experiment.py:run_experiment"


def _sketch(source: str, **extra: Any) -> dict:
    """The answer of a module author that declares `source`: a sketch (§XXIX D5), with what else it returns."""
    return {**sketch_of(source), **extra}


def _base_plan() -> dict:
    return {
        "interfaces": {"src/mod_a.py": _MOD_A, "src/mod_b.py": _MOD_B, "src/experiment.py": _EXP, "src/figures.py": _PLOTS},
        "entrypoint": _ENTRY,
        "plots": "src/figures.py:plots",
        "academic_blueprint": {
            "thesis_statement": "A+B=3", "metrics": ["score"],
            "planned_chapters": [{"index": 1, "title": "Wstęp"}, {"index": 2, "title": "Wyniki eksperymentu"}],
        },
    }


Answer = Callable[[dict[str, Any], int], Any]


def _run(orch: NeuroSymbolicOrchestrator, plan: dict, overrides: dict[str, Answer] | None = None) -> tuple[Any, list[tuple[str, dict]]]:
    """`_staged_plan` with the planning agents answering `plan` stage by stage, except the `overrides` (agent ->
    f(payload, call number of that agent)). Returns (result, calls as (agent, payload))."""
    calls: list[tuple[str, dict]] = []

    def fake(md: Any, payload: dict, **_kw: Any) -> dict:
        agent = Path(md).stem
        calls.append((agent, payload))
        n = sum(1 for a, _ in calls if a == agent)
        if overrides and agent in overrides:
            out = overrides[agent](payload, n)
            if isinstance(out, BaseException):  # a failed call: `call_agent` returns it as an answer
                return {"status": "error", "error": str(out), "output": {}}
            if out is not None:
                return {"status": "ok", "output": out}
        return {"status": "ok", "output": staged_answer(plan, agent, payload)}

    orch._call_agent = fake
    orch._events_from = len(_lines(orch))  # the log is shared by the test session
    return orch._staged_plan({"user_prompt": "p", "detected_template": {"thesis_type": "inzynierska", "is_certain": True}}), calls


def _lines(orch: NeuroSymbolicOrchestrator) -> list[str]:
    return orch.logger.events_path.read_text(encoding="utf-8").splitlines() if orch.logger.events_path.exists() else []


def _module_calls(calls: list[tuple[str, dict]]) -> list[str]:
    return [p["module"]["file"] for a, p in calls if a == "plan_module"]


def _critic_fail(where: str) -> dict:
    return {"status": "FAIL", "issues": [{"blocking": True, "category": "interfaces", "where": where, "problem": "broken", "fix": "fix it"}]}
