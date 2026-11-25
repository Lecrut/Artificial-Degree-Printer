"""Story: a run in which the first answers are wrong the way a small model is wrong (a stub left in, a broken signature): the harness repairs them, verifies the repaired tasks and the run completes; the events tell what happened."""

from __future__ import annotations

import json
from pathlib import Path

from adk.core.logger import set_process_log_dir
from adk.orchestrator import NeuroSymbolicOrchestrator
from main import run_scenario
from tests.support.adk_sandbox import _clone_adk_env


def _events(log_dir: Path) -> list[dict]:
    path = log_dir / "events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


_E2E_GAME = (
    "from src.config import N_GAMES\n\n\ndef play(seed: int) -> int:\n"
    '    """Wins in N_GAMES games, never negative."""\n    ...\n'
)


_E2E_EXPERIMENT = 'from src.config import SEEDS\nfrom src.game import play\n\n\ndef run_experiment() -> list[int]:\n    """Wins per seed."""\n    ...\n'


_E2E_IFACES = {"src/config.py": "N_GAMES: int = 3\nSEEDS: list[int] = [0, 1]\n", "src/game.py": _E2E_GAME, "src/experiment.py": _E2E_EXPERIMENT}


_E2E_IMPL = {
    "src/config.py": _E2E_IFACES["src/config.py"],
    "src/game.py": 'from src.config import N_GAMES\n\n\ndef play(seed: int) -> int:\n    """Wins."""\n    return (seed + N_GAMES) % 2\n',
    "src/experiment.py": 'from src.config import SEEDS\nfrom src.game import play\n\n\ndef run_experiment() -> list[int]:\n    """Wins."""\n    return [play(s) for s in SEEDS]\n',
}


def _e2e(tmp_path: Path, implement_entry: bool = True) -> tuple[dict, list[str], list[dict]]:
    from adk.core.llm import set_llm_handler
    from adk.mocks.staged import staged_answer
    from adk.orchestrator import NeuroSymbolicOrchestrator

    built: list[str] = []

    plan = {"interfaces": _E2E_IFACES, "entrypoint": "src/experiment.py:run_experiment", "plots": "src/experiment.py:run_experiment"}

    def handler(agent, _system_prompt, payload, _tier):
        staged = staged_answer(plan, agent, payload)
        if staged is not None:
            return staged
        target = str(payload.get("target_file") or "")
        built.append(target)
        if target.startswith("tests/"):
            return {"test_code": "from src.game import play\n\n\ndef test_play():\n    assert play(0) >= 0\n", "test_file": target}
        if target in _E2E_IMPL:
            source = _E2E_IMPL[target] if implement_entry or target != "src/experiment.py" else _E2E_EXPERIMENT
            return {"files": [{"filename": target, "content": source}], "summary": "impl"}
        return {"status": "PASS", "issues": []}

    log_dir = tmp_path / "logs"
    set_process_log_dir(log_dir)
    set_llm_handler(handler)
    try:
        orch = NeuroSymbolicOrchestrator(adk_root=_clone_adk_env(tmp_path), enable_layer4=False, include_docs=False, provider="mock")
        result = orch.run("Gra i eksperyment", multi_cycle_waves=True, interactive_gates=False, max_replan_retries=2)
    finally:
        set_llm_handler(None)
        set_process_log_dir(None)
    return result, built, _events(log_dir)


def test_run_writes_task_outcomes_and_verdicts_to_events(tmp_path: Path):
    """T3: the process log had 86 verification starts and not one verdict; outcomes must be machine-readable."""
    log_dir = tmp_path / "logs"
    set_process_log_dir(log_dir)
    try:
        result = run_scenario("1", provider="mock", adk_root=_clone_adk_env(tmp_path))
    finally:
        set_process_log_dir(None)
    assert result["status"] == "COMPLETED"
    kinds = [e["event"] for e in _events(log_dir)]
    assert "TASK_START" in kinds and "VERDICT" in kinds and "TASK_DONE" in kinds
    verdict = next(e for e in _events(log_dir) if e["event"] == "VERDICT")
    assert verdict["status"] in ("PASS", "FAIL") and verdict["task_id"]


def test_the_entrypoint_runs_after_what_it_uses_and_every_task_sees_its_specification(tmp_path: Path):
    result, built, events = _e2e(tmp_path)
    assert result["status"] == "COMPLETED"
    # the derived queue (§XVI): every module after what it uses, its tests right after it, the entrypoint last
    assert built[:4] == ["src/config.py", "src/game.py", "tests/test_game.py", "src/experiment.py"]
    verified = {e["vertex"] for e in events if e["event"] == "VERTEX_STATE" and e["state"] == "verified"}
    assert {"src/config.py", "src/game.py", "src/experiment.py"} <= verified


def test_an_unimplemented_entrypoint_never_completes_the_run(tmp_path: Path):
    """01: the entrypoint stayed `raise NotImplementedError` for the whole run."""
    result, _built, events = _e2e(tmp_path, implement_entry=False)
    assert result["status"] != "COMPLETED"
    assert any(e["event"] == "VERDICT" and "NOT_IMPLEMENTED" in str(e.get("first_issue")) for e in events)


def test_orchestrator_wave1_and_wave2_loops(tmp_path: Path):
    """The coder's first answer for the entrypoint keeps its stubs: verification fails (NOT_IMPLEMENTED), the author
    repairs it once and the run completes, with and without Layer 4. Mutation is covered at the tool level
    (test_rule_naming_*, test_missing_rule_* below)."""
    from adk.mocks import install_simulated_agents

    adk_dir = _clone_adk_env(tmp_path)
    history_path = adk_dir / "state" / "evolution_history.json"

    install_simulated_agents(flaws={"coder_leaves_stub"})
    orch_w1 = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=False, provider="mock")
    res_w1 = orch_w1.run("Zbuduj moduł walidacji parametrów")
    assert res_w1["status"] == "COMPLETED"
    assert res_w1["replan_count"] == 1
    assert [c["w4_action"] for c in res_w1["architecture_cycles"]] == ["FAST_FIX"]
    assert all(t["status"] == "DONE" for t in res_w1["tasks"])

    # A second project in its own workspace: on the first one's workspace its modules exist and are kept (§XVI).
    adk_dir = _clone_adk_env(tmp_path / "second")
    history_path = adk_dir / "state" / "evolution_history.json"
    seen = len(json.loads(history_path.read_text(encoding="utf-8"))["events"])
    install_simulated_agents(flaws={"coder_leaves_stub"})
    orch_w2 = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, provider="mock")
    res_w2 = orch_w2.run("Rozbuduj moduł o wykresy i raport", missing_agent_specialization="latex_table_formatter")
    assert res_w2["status"] == "COMPLETED"
    assert res_w2["replan_count"] == 1
    new_events = [e["type"] for e in json.loads(history_path.read_text(encoding="utf-8"))["events"][seen:]]
    assert new_events == ["AGENT_CREATED"]

    res_hitl = orch_w2.run("Sprzeczne wymagania", contradictory_requirements=True)
    assert res_hitl["status"] == "HITL_PAUSED"
    hitl_data = json.loads((adk_dir / "state" / "hitl_flag.json").read_text(encoding="utf-8"))
    assert hitl_data["active"] is True


def test_interactive_gates_callback_and_repair_of_a_failed_task_in_orchestrator(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)

    # 1. A task that fails in Layer 3 is repaired by its author and the run still completes
    from adk.mocks import install_simulated_agents

    install_simulated_agents(flaws={"coder_leaves_stub"})
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=False, provider="mock")
    res = orch.run("Test repair of a failed task")
    assert res["status"] == "COMPLETED"
    assert any(c["w4_action"] == "FAST_FIX" for c in res["architecture_cycles"])

    # 2. Verify gate_approval_callback can pause execution at GATE_2_METHODOLOGY_APPROVAL
    visited_gates: list[str] = []

    def _reject_gate2(gate_name: str, _ctx: dict) -> bool:
        visited_gates.append(gate_name)
        return gate_name != "GATE_2_METHODOLOGY_APPROVAL"

    res_paused = orch.run(
        "Test HITL gate rejection",
        gate_approval_callback=_reject_gate2,
    )
    assert res_paused["status"] == "HITL_PAUSED"
    assert res_paused["gate"] == "GATE_2_METHODOLOGY_APPROVAL"
    assert "GATE_1_OUTLINE_APPROVAL" in visited_gates
    assert "GATE_2_METHODOLOGY_APPROVAL" in visited_gates
