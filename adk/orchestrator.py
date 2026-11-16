from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from adk.orchestration import agent_texts as texts
from adk.core.connection import LLMConnectionManager
from adk.core.llm import call_agent
from adk.core.logger import get_process_logger
from adk.core.models import read_json_state, write_json_state
from adk.tools.planning import (
    select_model_tier,
)
from adk.orchestration.common import (
    _merge_bibtex_entries,
    _issue_signature,
    _collect_report_issues,
    _fit_items,
    THESIS_FILE,
    _declared_vs_measured_metrics,
    _missing_chapter_tasks,
    _RunState,
    _agent_for_path,
    MaterializationError,
    build_grounded_symbols,
)
from adk.orchestration.gates import GatesMixin
from adk.orchestration.routing import RoutingMixin
from adk.orchestration.building import BuildingMixin
from adk.orchestration.contract_gate import ContractGateMixin
from adk.orchestration.write_gate import WriteGateMixin
from adk.orchestration.verification import VerificationMixin
from adk.orchestration.factual_audit import FactualAuditMixin
from adk.orchestration.evolution import EvolutionMixin
from adk.orchestration.planning import PlanningMixin
from adk.orchestration.plan_healing import PlanHealingMixin
from adk.orchestration.recovery import RecoveryMixin
from adk.orchestration.repair import RepairMixin

__all__ = [
    "NeuroSymbolicOrchestrator",
    "_merge_bibtex_entries",
    "_issue_signature",
    "_collect_report_issues",
    "_fit_items",
    "_declared_vs_measured_metrics",
    "MaterializationError",
    "build_grounded_symbols",
]


class NeuroSymbolicOrchestrator(
    PlanningMixin,
    PlanHealingMixin,
    BuildingMixin,
    WriteGateMixin,
    ContractGateMixin,
    VerificationMixin,
    FactualAuditMixin,
    RepairMixin,
    EvolutionMixin,
    RecoveryMixin,
    RoutingMixin,
    GatesMixin,
):
    """Main control loop for the Python-only Neuro-Symbolic Harness.

    The run loop lives here; each layer is a mixin in adk/orchestration/."""

    def __init__(
        self,
        adk_root: str | Path | None = None,
        enable_layer4: bool = True,
        include_docs: bool = True,
        provider: str | None = None,
        max_replan_retries: int = 5,
        interactive_gates: bool = False,
        gate_approval_callback: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> None:
        self.adk_root = Path(adk_root) if adk_root else Path(__file__).resolve().parent
        self.state_dir = self.adk_root / "state"
        self.agents_dir = self.adk_root / "agents"
        self.workspace_dir = self.adk_root / "workspace"
        self.enable_layer4 = enable_layer4
        self.include_docs = include_docs
        conn = LLMConnectionManager(provider=provider)
        self.provider = conn.resolve_provider()
        self.max_replan_retries = max_replan_retries
        self.interactive_gates = interactive_gates
        self.gate_approval_callback = gate_approval_callback
        self.current_user_prompt: str = ""
        self.logger = get_process_logger()

        self.matrix_path = self.state_dir / "hypergraph_matrix.json"
        self.task_queue_path = self.state_dir / "task_queue.json"
        self.registry_path = self.state_dir / "agent_registry.json"
        self.validation_report_path = self.state_dir / "validation_report.json"
        self.failure_ledger_path = self.state_dir / "failure_ledger.json"
        self.evolution_history_path = self.state_dir / "evolution_history.json"
        self.hitl_flag_path = self.state_dir / "hitl_flag.json"
        self.blueprint_path = self.state_dir / "academic_blueprint.json"
        self._last_experiment_error = ""
        # Files written since the last verification: together with the task's node they are its verification scope.
        self._written_since_verification: set[str] = set()

    def _call_agent(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """The single seam through which every part of the orchestrator calls a model (tests patch `call_agent`)."""
        return call_agent(*args, **kwargs)

    def run(
        self,
        user_prompt: str,
        target_node: str = "v1",
        simulate_first_attempt_fail: bool = False,
        missing_agent_specialization: str | None = None,
        contradictory_requirements: bool = False,
        max_replan_retries: int | None = None,
        interactive_gates: bool | None = None,
        gate_approval_callback: Callable[[str, dict[str, Any]], bool] | None = None,
        multi_cycle_waves: bool = False,
        template_name: str | None = None,
        thesis_type: str | None = None,
    ) -> dict[str, Any]:
        """Execute the full Neuro-Symbolic Harness pipeline: plan, build and verify each task, defend, deliver."""
        self.current_user_prompt = user_prompt
        self.multi_cycle_waves = multi_cycle_waves
        self.logger.log_step(
            "ORCHESTRATOR_START",
            f"Start scenariusza: enable_layer4={self.enable_layer4}, include_docs={self.include_docs}, multi_cycle_waves={multi_cycle_waves}",
            {"user_prompt": user_prompt, "target_node": target_node, "multi_cycle_waves": multi_cycle_waves},
        )
        if contradictory_requirements and self.enable_layer4:
            l4_res = self._run_evolution_step({"contradictory_requirements": True, "user_prompt": user_prompt})
            return {"status": "HITL_PAUSED", "layer4": l4_res}

        planned = self._plan_phase(
            user_prompt,
            target_node=target_node,
            missing_agent_specialization=missing_agent_specialization,
            interactive_gates=interactive_gates,
            gate_approval_callback=gate_approval_callback,
            multi_cycle_waves=multi_cycle_waves,
            template_name=template_name,
            thesis_type=thesis_type,
        )
        if "stop" in planned:
            return planned["stop"]

        state = _RunState(
            user_prompt=user_prompt,
            max_retries=self.max_replan_retries if max_replan_retries is None else int(max_replan_retries),
            multi_cycle_waves=multi_cycle_waves,
            tasks=planned["tasks"],
        )
        self._print_queue(state.tasks)
        injected_failures = self._simulated_failure_indices(state.tasks, simulate_first_attempt_fail, multi_cycle_waves)

        while True:
            # Layers 2 -> 3 -> [4] -> 1 -> 2 -> 3 for every task of the current queue generation.
            for idx, task in enumerate(state.tasks):
                if task.get("status") == "BLOCKED":
                    continue
                stop = self._execute_task(state, idx, task, inject_failure=state.generation == 0 and idx in injected_failures)
                if stop is not None:
                    return stop

            # A failed task leaves the workspace in an unknown state: audit it before defending the thesis.
            if any(isinstance(t, dict) and t.get("status") == "FAILED" for t in state.tasks):
                health = self._run_verification_step(
                    state.tasks[-1] if state.tasks else {"target_node": self._role_file("core"), "task_id": "QUEUE_FINAL"},
                    include_docs=self.include_docs,
                    is_final_gate=False,
                    inject_failure=False,
                )
                if health.get("status") != "PASS":
                    stop = self._next_generation(state, health)
                    if stop is not None:
                        return stop
                    continue

            # Final defense (Gate 3): full validation of code, results and every chapter, with repair cycles.
            final_report = self._defend(state, state.tasks[-1] if state.tasks else {"target_node": THESIS_FILE, "task_id": "FINAL_DEFENSE"})
            if final_report.get("status") == "PASS":
                pdf_report = self._pdf_failure_report()
                if pdf_report is not None:
                    print("  [PDF] Kompilacja nie przeszła. Audyt stanu i nowa kolejka.", flush=True)
                    stop = self._next_generation(state, pdf_report)
                    if stop is not None:
                        return stop
                    continue
            else:
                stop = self._next_generation(state, final_report)
                if stop is not None:
                    return stop
                continue

            if not self._check_hitl_gate(
                gate_name="GATE_3_DEFENSE_APPROVAL",
                context_payload={"validation_status": "PASS", "replan_count": state.replan_count},
                interactive_gates=interactive_gates,
                gate_approval_callback=gate_approval_callback,
            ):
                return state.outcome(
                    status="HITL_PAUSED",
                    gate="GATE_3_DEFENSE_APPROVAL",
                    hitl=read_json_state(self.hitl_flag_path),
                    validation_report=final_report,
                )

            self.logger.log_step(
                "ORCHESTRATOR_DONE",
                f"Zakończono scenariusz ze statusem COMPLETED (replan_count={state.replan_count}, cycles={len(state.architecture_cycles)}).",
            )
            return state.outcome(
                status="COMPLETED",
                mode={
                    "enable_layer4": self.enable_layer4,
                    "include_docs": self.include_docs,
                    "multi_cycle_waves": multi_cycle_waves,
                },
                validation_report=final_report,
                log_files={
                    "process_log": str(self.logger.text_log_path),
                    "agent_trace_jsonl": str(self.logger.trace_jsonl_path),
                },
            )

    def _print_queue(self, tasks: list[dict[str, Any]]) -> None:
        matrix_nodes = read_json_state(self.matrix_path).get("nodes", {})
        print("\n" + "=" * 80, flush=True)
        print(f"[KOLEJKA ZADAN ZATWIERDZONA] Laczna liczba zadan do wykonania: {len(tasks)}", flush=True)
        for i, t in enumerate(tasks, 1):
            n_id = str(t.get("target_node", "v1"))
            n_file = matrix_nodes.get(n_id, {}).get("path", n_id)
            print(
                f"  * Zadanie {t.get('task_id', f'T{i}')} ({i}/{len(tasks)}): "
                f"[{n_file}] {t.get('description', 'Brak opisu')} -> Agent: {t.get('assigned_agent', 'seed_coder')}",
                flush=True,
            )
        print("=" * 80 + "\n", flush=True)

    def _simulated_failure_indices(
        self, tasks: list[dict[str, Any]], simulate_first_attempt_fail: bool, multi_cycle_waves: bool
    ) -> set[int]:
        """Queue positions whose first verification is forced to fail. Mock testing only, never in live runs."""
        if not simulate_first_attempt_fail or str(self.provider).strip().lower() != "mock":
            return set()
        if not multi_cycle_waves:
            return {0}
        roles = [self._role_of(t.get("target_node")) for t in tasks]
        config_idx = next((i for i, r in enumerate(roles) if r == "config"), 0)
        # No task targets the results file any more (U5): the results wave is the module that writes them.
        results_idx = next(
            (i for role in ("results", "core") for i, r in enumerate(roles) if r == role and tasks[i].get("task_id") != "SKELETON"),
            min(2, len(tasks) - 1),
        )
        thesis_idx = next((i for i in range(len(roles) - 1, -1, -1) if roles[i] == "thesis"), len(tasks) - 1)
        return {config_idx, results_idx, thesis_idx}

    def _execute_task(self, state: _RunState, idx: int, task: dict[str, Any], inject_failure: bool) -> dict[str, Any] | None:
        """Build one task, verify it, repair it within budget. Returns a terminal payload only for a promotor pause."""
        task["status"] = "IN_PROGRESS"
        write_json_state(self.task_queue_path, state.tasks)

        node_id, node_file = self._resolve_target_node(str(task.get("target_node", "v1")), task=task, fallback="v1")
        task["target_node"] = node_id
        tier = select_model_tier()
        t_id = str(task.get("task_id", f"T{idx + 1}"))
        t_agent = str(task.get("assigned_agent", "seed_coder"))
        print(
            f"\n>>> [ZADANIE {t_id}] ({idx + 1}/{len(state.tasks)}): {task.get('description', 'Brak opisu')}\n"
            f"    Plik/Wezel: {node_file} ({node_id}) | Agent: {t_agent} | Model Tier: {tier}",
            flush=True,
        )
        print(f"  [WARSTWA 2: BUDOWANIE] Generowanie implementacji przez agenta '{t_agent}'...", flush=True)

        builder_error_msg: str | None = None
        try:
            self._execute_builder_step(task, model_tier=tier)
            self._refresh_experiment_after_code(node_id)
        except Exception as exc:
            builder_error_msg = texts.task_exception(t_id, node_id, node_file, exc)
            print(f"  [OSTRZEŻENIE: BŁĄD BUDOWANIA] {builder_error_msg}", flush=True)

        print(f"  [WARSTWA 3: WERYFIKACJA] Audyt zadania {t_id} (pytest + ruff + kompilator symboliczny)...", flush=True)
        report = self._run_verification_step(
            task, include_docs=self.include_docs, is_final_gate=False, inject_failure=inject_failure
        )
        if builder_error_msg:
            report["status"] = "FAIL"
            report["failed_agent"] = report.get("failed_agent") or t_agent
            report.setdefault("issues", []).append(builder_error_msg)
            report.setdefault("errors", []).append(builder_error_msg)

        report, stop = self._repair_task(state, task, report, node_id, node_file)
        if stop is not None:
            return stop

        if report["status"] == "PASS":
            task["status"] = "DONE"
            write_json_state(self.task_queue_path, state.tasks)
            print(f"  [ZADANIE {t_id} ZATWIERDZONE] Status: DONE (Weryfikacja zakonczona sukcesem)", flush=True)
            return None

        # A failed task blocks only the remaining tasks on the same file; the rest of the queue still runs
        # (a `break` here used to kill e.g. the test-fixing task queued right after a code task).
        task["status"] = "FAILED"
        same_file = [
            t
            for t in state.tasks[idx + 1 :]
            if isinstance(t, dict) and t.get("status") == "TODO" and str(t.get("target_node")) in (node_id, node_file)
        ]
        for blocked in same_file:
            blocked["status"] = "BLOCKED"
            blocked["blocked_by"] = t_id
        write_json_state(self.task_queue_path, state.tasks)
        print(
            f"  [ZADANIE {t_id} NIENAPRAWIONE] po {task.get('repair_attempts', 0)} próbach. Wstrzymano {len(same_file)} "
            f"zadań na pliku {node_file}; pozostałe zadania kolejki idą dalej.",
            flush=True,
        )
        return None


    def _defend(self, state: _RunState, defense_task: dict[str, Any]) -> dict[str, Any]:
        """Gate 3: full validation of code, results and every chapter, repaired with the shared repair cycle."""
        print(
            "\n  [WARSTWA 3: BRAMKA KONCOWA OBRONY PRACY (GATE_3_DEFENSE_APPROVAL)] Pelna walidacja kodu, CSV i 6 rozdzialow pracy...",
            flush=True,
        )
        final_report = self._run_verification_step(defense_task, include_docs=self.include_docs, is_final_gate=True, inject_failure=False)
        retries = 0
        while final_report.get("status") != "PASS" and retries < state.max_retries:
            retries += 1
            state.replan_count += 1
            issues = _collect_report_issues(final_report)
            shown = "; ".join(_fit_items(issues)) or texts.DEFENSE_DEFECT
            print(
                f"\n  [WARSTWA 3 -> ODRZUCENIE OBRONY GATE 3] Proba naprawy #{retries}: {shown}\n"
                f"  [POWROT DO WARSTWY 1: REMEDIACJA OBRONY] Synteza zadan naprawczych dla Gate 3...",
                flush=True,
            )
            def_node, def_file = self._resolve_target_node(str(final_report.get("failed_file") or THESIS_FILE), fallback=THESIS_FILE)
            errors = self._repair_cycle(
                state,
                final_report,
                failed_task={
                    "task_id": f"GATE_3_FIX_{retries}",
                    "target_node": def_node,
                    "assigned_agent": _agent_for_path(def_file),
                },
                node_id=def_node,
                directive=texts.defense_directive(shown),
                fallback_description=texts.defense_fallback(shown),
                extra_tasks=_missing_chapter_tasks("; ".join(issues)),
                append_to_queue=state.multi_cycle_waves,
            )
            print(f"  [WARSTWA 3: RE-AUDYT GATE 3] Ponowna weryfikacja obrony po naprawie #{retries}...", flush=True)
            final_report = self._run_verification_step(
                defense_task, include_docs=self.include_docs, is_final_gate=True, inject_failure=False
            )
            if errors:
                final_report.setdefault("warnings", []).extend(errors)
        if final_report.get("status") != "PASS":
            print(
                f"  [KOLEJKA PRZERWANA] Obrona Gate 3 nie przeszła po {retries} próbach. Audyt stanu i nowa kolejka.",
                flush=True,
            )
        return final_report
