from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import patch

from adk.orchestrator import NeuroSymbolicOrchestrator


def _setup_test_orchestrator(tmp_path: Path) -> NeuroSymbolicOrchestrator:
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
    # The hypergraph is state too: without this the tests rewrote the repository seed adk/state/hypergraph_matrix.json.
    orch.matrix_path = orch.state_dir / "hypergraph_matrix.json"
    shutil.copy2(Path("adk") / "state" / "hypergraph_matrix.json", orch.matrix_path)
    return orch


def test_intermediate_task_ignores_pending_future_dependencies(tmp_path: Path) -> None:
    """Verify that intermediate tasks (is_final_gate=False) do not fail due to unmaterialized future task files."""
    orch = _setup_test_orchestrator(tmp_path)

    tasks = [
        {"task_id": "T1", "target_node": "v4", "assigned_agent": "background_researcher", "status": "IN_PROGRESS"},
        {"task_id": "T2", "target_node": "v1", "assigned_agent": "seed_coder", "status": "TODO"},
        {"task_id": "T3", "target_node": "v2", "assigned_agent": "seed_coder", "status": "TODO"},
        {"task_id": "T4", "target_node": "v3", "assigned_agent": "seed_tester", "status": "TODO"},
        {"task_id": "T5", "target_node": "v4", "assigned_agent": "seed_writer", "status": "TODO"},
    ]
    orch.task_queue_path.write_text(json.dumps(tasks), encoding="utf-8")

    doc_path = orch.workspace_dir / "thesis.md"
    doc_path.write_text(
        "# Wstęp\nParametr: \\ref_ast{config.py:ALPHA}, wynik: \\ref_csv{results.csv:accuracy}.\n",
        encoding="utf-8",
    )

    report = orch._run_verification_step(tasks[0], include_docs=True, is_final_gate=False)
    assert report["status"] == "PASS"

    val_data = json.loads(orch.validation_report_path.read_text(encoding="utf-8"))
    assert val_data["status"] == "PASS"
    assert val_data["supervisors"]["redteam_critic_guard"]["status"] == "SKIPPED_INTERMEDIATE_TASK"


def test_final_defense_gate_enforces_all_references_and_redteam(tmp_path: Path) -> None:
    """Verify that Gate 3 final defense (is_final_gate=True) strictly validates missing files and runs redteam."""
    orch = _setup_test_orchestrator(tmp_path)

    tasks = [
        {"task_id": "T1", "target_node": "v4", "assigned_agent": "background_researcher", "status": "DONE"},
        {"task_id": "T2", "target_node": "v1", "assigned_agent": "seed_coder", "status": "DONE"},
        {"task_id": "T3", "target_node": "v2", "assigned_agent": "seed_coder", "status": "DONE"},
        {"task_id": "T4", "target_node": "v3", "assigned_agent": "seed_tester", "status": "DONE"},
        {"task_id": "T5", "target_node": "v4", "assigned_agent": "seed_writer", "status": "DONE"},
    ]
    orch.task_queue_path.write_text(json.dumps(tasks), encoding="utf-8")

    doc_path = orch.workspace_dir / "thesis.md"
    doc_path.write_text("# Wstęp\nParametr: \\ref_ast{config.py:ALPHA}\n", encoding="utf-8")

    report = orch._run_verification_step(tasks[-1], include_docs=True, is_final_gate=True)
    assert report["status"] == "FAIL"

    val_data = json.loads(orch.validation_report_path.read_text(encoding="utf-8"))
    assert val_data["status"] == "FAIL"
    assert val_data["supervisors"]["symbolic_auditor"]["status"] == "FAIL"


def test_lightweight_planning_payload_and_blueprint_persistence(tmp_path: Path) -> None:
    """Verify Phase 1: plan_payload is lightweight and contains domain_context with suggested_sections."""
    orch = _setup_test_orchestrator(tmp_path)

    captured_payloads: list[dict[str, Any]] = []

    def mock_call_agent(_agent_md: Any, payload: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        captured_payloads.append(payload)
        return {
            "output": {
                "thesis_type": "inzynierska",
                "academic_blueprint": {
                    "thesis_title": "Badanie RL",
                    "thesis_statement": "Q-learning osiąga zbieżność",
                    "planned_chapters": [
                        {"index": 1, "title": "Wstęp i Cel Pracy"},
                        {"index": 2, "title": "Przegląd Literatury"},
                        {"index": 3, "title": "Implementacja i Wyniki"},
                        {"index": 4, "title": "Wnioski"},
                    ],
                },
                "tasks": [
                    {"task_id": "T1", "description": "Lit", "target_node": "v4", "assigned_agent": "background_researcher", "status": "TODO"},
                    {"task_id": "T2", "description": "Cfg", "target_node": "v1", "assigned_agent": "seed_coder", "status": "TODO"},
                    {"task_id": "T3", "description": "Core", "target_node": "v2", "assigned_agent": "seed_coder", "status": "TODO"},
                    {"task_id": "T4", "description": "Test", "target_node": "v3", "assigned_agent": "seed_tester", "status": "TODO"},
                    {"task_id": "T5", "description": "Doc", "target_node": "v4", "assigned_agent": "seed_writer", "status": "TODO"},
                ],
            }
        }

    with patch("adk.orchestrator.call_agent", side_effect=mock_call_agent):
        orch.run("01_rl_tictactoe", target_node="v1", multi_cycle_waves=False)

    planner_payload = captured_payloads[0]
    assert "domain_context" in planner_payload
    assert "suggested_sections" in planner_payload["domain_context"]
    assert orch.blueprint_path.exists()
    saved_blueprint = json.loads(orch.blueprint_path.read_text(encoding="utf-8"))
    assert "table_of_contents" in saved_blueprint
    # Dynamic 4 chapters planned by task_planner were stored in table_of_contents
    chapters = saved_blueprint["table_of_contents"]["chapters"]
    assert len(chapters) == 4
    assert chapters[0]["title"] == "Wstęp i Cel Pracy"
    assert chapters[3]["title"] == "Wnioski"


def test_dynamic_chapter_planning_adapts_to_custom_structure(tmp_path: Path) -> None:
    """Verify that task_planner can define custom chapters (e.g. 5 chapters for paper) without hardcoding 6 chapters."""
    orch = _setup_test_orchestrator(tmp_path)

    custom_chapters = [
        {"index": 1, "title": "Introduction", "focus": "Background and thesis"},
        {"index": 2, "title": "Related Work", "focus": "2023-2026 competitors"},
        {"index": 3, "title": "Methodology", "focus": "Core mathematical algorithm"},
        {"index": 4, "title": "Experiments", "focus": "Comparative benchmarks"},
        {"index": 5, "title": "Conclusion", "focus": "Future research directions"},
    ]

    def mock_call_agent(_agent_md: Any, _payload: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        return {
            "output": {
                "thesis_type": "paper",
                "academic_blueprint": {
                    "thesis_title": "Efficient Reinforcement Learning in Discrete State Spaces",
                    "planned_chapters": custom_chapters,
                },
                "tasks": [
                    {"task_id": "T1", "description": "Related work review", "target_node": "v4", "assigned_agent": "discoverer_researcher", "status": "TODO"},
                    {"task_id": "T2", "description": "Configuration AST", "target_node": "v1", "assigned_agent": "seed_coder", "status": "TODO"},
                    {"task_id": "T3", "description": "Core algorithm", "target_node": "v2", "assigned_agent": "seed_coder", "status": "TODO"},
                    {"task_id": "T4", "description": "Empirical benchmarks", "target_node": "v3", "assigned_agent": "seed_tester", "status": "TODO"},
                    {"task_id": "T5", "description": "Paper drafting according to planned_chapters", "target_node": "v4", "assigned_agent": "seed_writer", "status": "TODO"},
                ],
            }
        }

    with patch("adk.orchestrator.call_agent", side_effect=mock_call_agent):
        orch.run("01_rl_tictactoe", target_node="v1", multi_cycle_waves=False)

    saved_blueprint = json.loads(orch.blueprint_path.read_text(encoding="utf-8"))
    assert saved_blueprint["thesis_type"] == "paper"
    chapters = saved_blueprint["table_of_contents"]["chapters"]
    assert len(chapters) == 5
    assert [c["title"] for c in chapters] == [
        "Introduction",
        "Related Work",
        "Methodology",
        "Experiments",
        "Conclusion",
    ]

def test_reflexive_prompt_evolution_recovers_empty_tasks(tmp_path: Path) -> None:
    """Verify that when task_planner initially returns empty tasks, the reflexive re-prompting loop recovers valid tasks with feedback."""
    orch = _setup_test_orchestrator(tmp_path)

    call_count = 0
    captured_payloads: list[dict[str, Any]] = []

    def mock_call_agent(_agent_md: Any, payload: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        captured_payloads.append(payload)
        if call_count == 1:
            # First attempt: LLM returned empty tasks due to token starvation
            return {
                "status": "ok",
                "output": {
                    "thesis_type": "inzynierska",
                    "tasks": [],
                    "academic_blueprint": {
                        "thesis_title": "Badanie RL",
                        "planned_chapters": [{"index": 1, "title": "Wstęp"}],
                    },
                },
            }
        else:
            # Second attempt (reflexive prompt evolution): returns recovered tasks
            return {
                "status": "ok",
                "output": {
                    "thesis_type": "inzynierska",
                    "tasks": [
                        {"task_id": "T1", "description": "Model", "target_node": "v1", "assigned_agent": "seed_coder", "status": "TODO"},
                        {"task_id": "T2", "description": "Core", "target_node": "v2", "assigned_agent": "seed_coder", "status": "TODO"},
                        {"task_id": "T3", "description": "Tests", "target_node": "v3", "assigned_agent": "seed_tester", "status": "TODO"},
                    ],
                    "academic_blueprint": {
                        "thesis_title": "Badanie RL - Evolved",
                        "planned_chapters": [{"index": 1, "title": "Wstęp"}],
                    },
                },
            }

    with patch("adk.orchestrator.call_agent", side_effect=mock_call_agent):
        orch.run("01_rl_tictactoe", target_node="v1", multi_cycle_waves=False)

    assert call_count >= 2
    # Verify reflection feedback was included in the second call
    assert "reflection_feedback" in captured_payloads[1]
    assert "BŁĄD" in captured_payloads[1]["reflection_feedback"]

    saved_queue = json.loads(orch.task_queue_path.read_text(encoding="utf-8"))
    assert len(saved_queue) >= 3
    assert saved_queue[0]["task_id"] == "T1"
    assert saved_queue[1]["task_id"] == "T2"


def test_elastic_task_count_preserves_custom_8_or_16_tasks_and_heals_missing_chapters(tmp_path: Path) -> None:
    """Verify that _normalize_and_heal_task_plan never forces a rigid 12-task count, preserving 9 or 16 tasks or injecting only missing chapters."""
    orch = _setup_test_orchestrator(tmp_path)

    # 1. A 9-task plan that already covers all nodes and chapters 1..6 -> stays 9 tasks!
    nine_tasks = [
        {"task_id": "T1", "description": "Rozdział 2: Przegląd literatury SOTA", "target_node": "v4", "assigned_agent": "background_researcher"},
        {"task_id": "T2", "description": "Rozdział 1: Wstęp, cel i teza pracy", "target_node": "v4", "assigned_agent": "seed_writer"},
        {"task_id": "T3", "description": "Parametry w config.py", "target_node": "v1", "assigned_agent": "seed_coder"},
        {"task_id": "T4", "description": "Algorytm w core.py", "target_node": "v2", "assigned_agent": "seed_coder"},
        {"task_id": "T5", "description": "Rozdział 3: Architektura systemu", "target_node": "v4", "assigned_agent": "seed_writer"},
        {"task_id": "T6", "description": "Rozdział 4: Implementacja algorytmu", "target_node": "v4", "assigned_agent": "seed_writer"},
        {"task_id": "T7", "description": "Ewaluacja results.csv i test_core.py", "target_node": "v3", "assigned_agent": "seed_tester"},
        {"task_id": "T8", "description": "Rozdział 5: Badania eksperymentalne i wyniki", "target_node": "v4", "assigned_agent": "seed_writer"},
        {"task_id": "T9", "description": "Rozdział 6: Podsumowanie i wnioski", "target_node": "v4", "assigned_agent": "seed_writer"},
    ]
    healed_9 = orch._normalize_and_heal_task_plan(
        nine_tasks, user_prompt="Test 9 tasks", multi_cycle_waves=True, thesis_type="inzynierska"
    )
    assert len(healed_9) == 9

    # 2. A 16-task granular plan -> stays 16 tasks!
    sixteen_tasks = nine_tasks + [
        {"task_id": f"T_EXTRA_{i}", "description": f"Dodatkowy podmoduł algorytmu #{i} w core.py", "target_node": "v2", "assigned_agent": "seed_coder"}
        for i in range(1, 8)
    ]
    healed_16 = orch._normalize_and_heal_task_plan(
        sixteen_tasks, user_prompt="Test 16 tasks", multi_cycle_waves=True, thesis_type="inzynierska"
    )
    assert len(healed_16) == 16

    # 3. A 7-task plan missing Chapters 5 and 6 -> only the 2 missing chapters are added (7 + 2 = 9 tasks, NOT 12)!
    seven_tasks_missing_5_6 = nine_tasks[:7]
    healed_7_to_9 = orch._normalize_and_heal_task_plan(
        seven_tasks_missing_5_6, user_prompt="Test 7 tasks", multi_cycle_waves=True, thesis_type="inzynierska"
    )
    assert len(healed_7_to_9) == 9




def test_healing_keeps_planner_order_and_builds_entrypoint_after_its_modules(tmp_path: Path) -> None:
    """Regression (2026-11-12 run): a healed plan was sorted by role, which put the experiment script before the
    environment and agent modules it imports, so the coder had nothing to import."""
    orch = _setup_test_orchestrator(tmp_path)
    orch.blueprint_path.write_text(json.dumps({"entrypoint": "run_experiment.py:main"}), encoding="utf-8")
    planned = [
        {"task_id": "T1", "description": "Literatura", "target_node": "thesis.md", "assigned_agent": "background_researcher"},
        {"task_id": "T2", "description": "Konfiguracja", "target_node": "config.py", "assigned_agent": "seed_coder"},
        {"task_id": "T3", "description": "Skrypt eksperymentu", "target_node": "run_experiment.py", "assigned_agent": "seed_coder"},
        {"task_id": "T4", "description": "Środowisko gry", "target_node": "envs/tictactoe_env.py", "assigned_agent": "seed_coder"},
        {"task_id": "T5", "description": "Testy środowiska", "target_node": "tests/test_env.py", "assigned_agent": "seed_tester"},
        {"task_id": "T6", "description": "Agent Q-learning", "target_node": "agents/q_agent.py", "assigned_agent": "seed_coder"},
        {"task_id": "T7", "description": "Rozdział 1-6 pracy", "target_node": "thesis.md", "assigned_agent": "seed_writer"},
    ]
    healed = orch._normalize_and_heal_task_plan(planned, user_prompt="RL", multi_cycle_waves=True)
    order = [t["target_node"] for t in healed]

    assert order.index("run_experiment.py") > order.index("agents/q_agent.py")
    assert order.index("run_experiment.py") > order.index("envs/tictactoe_env.py")
    # The planner's own order of the other tasks is kept; the healed results task comes after the code.
    assert order.index("envs/tictactoe_env.py") < order.index("tests/test_env.py") < order.index("agents/q_agent.py")
    assert order.index("results.csv") > order.index("run_experiment.py")
