"""Fixtures of the loop of a run: an orchestrator with a workspace, an evolution step with a given decision, a ruff finding."""

from __future__ import annotations

from pathlib import Path

from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.adk_sandbox import _clone_adk_env

_RUFF_F841 = (
    "Ruff lint failure: F841 Local variable `{name}` is assigned to but never used\n"
    "  --> adk\\workspace\\benchmarks\\_evolved_adk_state\\workspace\\plot_results.py:{line}:9\n"
)


def _orch_with_workspace(tmp_path: Path, files: dict[str, str]) -> NeuroSymbolicOrchestrator:
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    for rel, body in files.items():
        (orch.workspace_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (orch.workspace_dir / rel).write_text(body, encoding="utf-8")
    return orch


def _evolution_with_decision(tmp_path: Path, decision: dict) -> tuple[NeuroSymbolicOrchestrator, dict]:
    from adk.core.llm import set_llm_handler

    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    set_llm_handler(lambda *_args: decision)
    try:
        res = orch._run_evolution_step({"failed_agent": "seed_coder", "validation_report": {}})
    finally:
        set_llm_handler(None)
    return orch, res
