from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from adk.core.connection import LLMConnectionManager
from adk.core.llm import call_agent
from adk.core.logger import get_process_logger
from adk.core.models import read_json_state, write_json_state
from adk.tools.planning import (
    calculate_blast_radius,
    escalate_node_weight,
    get_scoped_hypergraph_context,
    select_model_tier,
)
from adk.orchestration.common import (
    _filter_bibtex,
    _merge_bibtex_entries,
    _RUFF_FINDING,
    _PYTEST_FINDING,
    _FILE_FINDING,
    _issue_fingerprints,
    _issue_signature,
    _collect_report_issues,
    _looks_like_workspace_path,
    GAPS_SECTION_TITLE,
    _KNOWN_EVOLUTION_ACTIONS,
    _NON_GENERAL_RULE,
    FINDINGS_BUDGET_CHARS,
    LOG_BUDGET_CHARS,
    _fit_items,
    _clip_log,
    _plain_text,
    _is_document,
    THESIS_FILE,
    ROLE_DEFAULTS,
    ROLE_ALIASES,
    _CONFIG_STEMS,
    _declared_vs_measured_metrics,
    _default_agent,
    _CHAPTER_REPAIR,
    _missing_chapter_tasks,
    _RunState,
    _agent_for_path,
    MaterializationError,
    OUTPUT_SCHEMA,
    _METADATA_KEYS,
    build_grounded_symbols,
)
from adk.orchestration.gates import GatesMixin
from adk.orchestration.routing import RoutingMixin
from adk.orchestration.building import BuildingMixin
from adk.orchestration.verification import VerificationMixin
from adk.orchestration.evolution import EvolutionMixin
from adk.orchestration.planning import PlanningMixin
from adk.orchestration.recovery import RecoveryMixin

__all__ = ["NeuroSymbolicOrchestrator", "_filter_bibtex", "_merge_bibtex_entries", "_RUFF_FINDING", "_PYTEST_FINDING", "_FILE_FINDING", "_issue_fingerprints", "_issue_signature", "_collect_report_issues", "_looks_like_workspace_path", "GAPS_SECTION_TITLE", "_KNOWN_EVOLUTION_ACTIONS", "_NON_GENERAL_RULE", "FINDINGS_BUDGET_CHARS", "LOG_BUDGET_CHARS", "_fit_items", "_clip_log", "_plain_text", "_is_document", "THESIS_FILE", "ROLE_DEFAULTS", "ROLE_ALIASES", "_CONFIG_STEMS", "_declared_vs_measured_metrics", "_default_agent", "_CHAPTER_REPAIR", "_missing_chapter_tasks", "_RunState", "_agent_for_path", "MaterializationError", "OUTPUT_SCHEMA", "_METADATA_KEYS", "build_grounded_symbols"]


class NeuroSymbolicOrchestrator(PlanningMixin, BuildingMixin, VerificationMixin, EvolutionMixin, RecoveryMixin, RoutingMixin, GatesMixin):
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
        results_idx = next((i for i, r in enumerate(roles) if r == "results"), min(2, len(tasks) - 1))
        thesis_idx = next((i for i in range(len(roles) - 1, -1, -1) if roles[i] == "thesis"), len(tasks) - 1)
        return {config_idx, results_idx, thesis_idx}

    def _execute_task(self, state: _RunState, idx: int, task: dict[str, Any], inject_failure: bool) -> dict[str, Any] | None:
        """Build one task, verify it, repair it within budget. Returns a terminal payload only for a promotor pause."""
        task["status"] = "IN_PROGRESS"
        write_json_state(self.task_queue_path, state.tasks)

        node_id, node_file = self._resolve_target_node(str(task.get("target_node", "v1")), task=task, fallback="v1")
        task["target_node"] = node_id
        tier = select_model_tier(node_id, self.matrix_path)
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
            builder_error_msg = f"Wyjątek wykonania zadania {t_id} na węźle {node_id} ({node_file}): {exc}"
            print(f"  [OSTRZEŻENIE: BŁĄD BUDOWANIA] {builder_error_msg}", flush=True)

        print(f"  [WARSTWA 3: WERYFIKACJA] Audyt zadania {t_id} (pytest + ruff + kompilator symboliczny)...", flush=True)
        report = self._run_verification_step(
            task, include_docs=self.include_docs, is_final_gate=False, inject_failure=inject_failure
        )
        if builder_error_msg:
            report["status"] = "FAIL"
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

    def _repair_task(
        self,
        state: _RunState,
        task: dict[str, Any],
        report: dict[str, Any],
        node_id: str,
        node_file: str,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """W3(FAIL) -> [contract fast fix | W4 evolution] -> W1 remediation -> W2 -> W3, until PASS or budget."""
        t_id = str(task.get("task_id", "T1"))
        t_desc = str(task.get("description", "Brak opisu"))
        task["repair_attempts"] = 0
        last_contract_fix: list[str] | None = None
        while report["status"] != "PASS" and task["repair_attempts"] < state.max_retries:
            task["status"] = "FAILED"
            write_json_state(self.task_queue_path, state.tasks)
            task["repair_attempts"] += 1
            state.replan_count += 1

            # EvoRoute: dynamically escalate node difficulty weight w(v) on failure
            esc_res = escalate_node_weight(node_id, delta=0.4, matrix_path=self.matrix_path)
            self._record_evolution_event({"type": "WEIGHT_ESCALATED", "details": esc_res})

            failed_agent = str(task.get("assigned_agent", "seed_coder"))
            state.agent_failures[failed_agent] = state.agent_failures.get(failed_agent, 0) + 1
            cycle_trace: dict[str, Any] = {
                "cycle_number": state.replan_count,
                "task_id": task.get("task_id"),
                "node_id": node_id,
                "node_file": node_file,
                "failed_agent": failed_agent,
                "w3_initial_status": "FAIL",
                "w4_action": "NONE",
                "w1_remediation_task_id": f"{t_id}_FIX",
                "w3_post_remediation_status": "PENDING",
            }
            print(
                f"  [WARSTWA 3 -> BLAD] Wykryto usterke w zadaniu {t_id} na wezle {node_id} ({node_file})!\n"
                f"    Eskalacja wagi EvoRoute w({node_id}) -> {esc_res.get('new_weight')}",
                flush=True,
            )

            issues_list = _collect_report_issues(report)
            issues_summary = "; ".join(_fit_items(issues_list)) if issues_list else "Usterka weryfikacji warstwy 3"
            remediation_directive = (
                f"Poprzednio nie zadziałało: {issues_summary}. "
                f"Zrób to: w zadaniu {t_id} na węźle {node_id} ({node_file}) wyeliminuj ten błąd i wygeneruj w pełni poprawną zawartość."
            )

            # Fast path: a hyperedge contract violation is deterministic and self-describing, so the same
            # builder is re-run with the exact message, skipping W4 + W1 (two LRM calls). A repeated
            # identical violation falls through to the full W4 -> W1 loop.
            contract_violations = report.get("contract_violations") or []
            if contract_violations and contract_violations != last_contract_fix:
                last_contract_fix = contract_violations
                contract_task = {
                    **task,
                    "task_id": f"{t_id}_CONTRACT_FIX",
                    "description": f"{t_desc}\nNAPRAW KONTRAKT HIPERGRAFU: " + " ".join(contract_violations),
                }
                print(
                    f"  [KONTRAKT HIPERKRAWĘDZI] {' '.join(contract_violations)}\n"
                    f"  [WARSTWA 2: SZYBKA NAPRAWA] Ponowne budowanie {node_file} bez W4/W1...",
                    flush=True,
                )
                self._record_evolution_event({"type": "CONTRACT_FAST_FIX", "task_id": t_id, "violations": contract_violations})
                try:
                    self._execute_builder_step(contract_task, model_tier=select_model_tier(node_id, self.matrix_path))
                    self._refresh_experiment_after_code(node_id)
                except Exception as exc:
                    # A crashed repair must not look like a completed one: keep it on record.
                    print(f"  [OSTRZEŻENIE: BŁĄD SZYBKIEJ NAPRAWY] {exc}", flush=True)
                    cycle_trace["builder_error"] = str(exc)
                    self._record_evolution_event({"type": "CONTRACT_FAST_FIX_FAILED", "task_id": t_id, "error": str(exc)})
                report = self._run_verification_step(task, include_docs=self.include_docs, is_final_gate=False, inject_failure=False)
                cycle_trace["w4_action"] = "CONTRACT_FAST_FIX"
                cycle_trace["w1_remediation_task_id"] = contract_task["task_id"]
                cycle_trace["w3_post_remediation_status"] = report["status"]
                state.architecture_cycles.append(cycle_trace)
                continue

            # W4 only for a failure this agent has not been disciplined for yet. The signature is the set
            # of `file:rule` fingerprints and every one seen in the run is remembered, so neither a
            # renamed identifier nor an A -> B -> A oscillation buys another near-identical MUTATE rule.
            evo_key = (failed_agent, _issue_signature({"issues": issues_list}))
            run_evolution = self.enable_layer4 and evo_key not in state.seen_evo
            if self.enable_layer4 and not run_evolution:
                cycle_trace["w4_action"] = "SKIPPED_SAME_FAILURE"
                print("  [WARSTWA 4: POMINIĘTA] Ten błąd był już w tym przebiegu; decyzja ewolucyjna już podjęta.", flush=True)
                state.repeats_after_evolution[evo_key] = state.repeats_after_evolution.get(evo_key, 0) + 1
                if state.repeats_after_evolution[evo_key] >= 2:
                    # The prompt was already changed for exactly this failure and it is still here: the defect
                    # is not in the agent. Stop spending retries on it and say where to look instead.
                    task["harness_bug"] = self._report_harness_bug(evo_key[1], t_id)
                    cycle_trace["w4_action"] = "REPORT_HARNESS_BUG"
                    state.architecture_cycles.append(cycle_trace)
                    break
            state.seen_evo.add(evo_key)

            if run_evolution:
                print(
                    f"  [WARSTWA 4: SAMOEWOLUCJA] Uruchomienie Architekta Ewolucji (cykl #{state.replan_count}, agent: {failed_agent})...",
                    flush=True,
                )
                evo_res = self._run_evolution_step(
                    {
                        "validation_report": report,
                        "failed_agent": failed_agent,
                        "agent_failure_count": state.agent_failures[failed_agent],
                        "cycle_index": state.replan_count,
                        "task_id": task.get("task_id"),
                        "target_node": node_id,
                        "suggested_rule": remediation_directive,
                    },
                    tasks_in_memory=state.tasks,
                )
                cycle_trace["w4_action"] = str(evo_res.get("action") or evo_res.get("decision") or "MUTATE_AGENT")
                if evo_res.get("action") == "REPORT_HARNESS_BUG":
                    task["harness_bug"] = evo_res.get("details", {})
                    state.architecture_cycles.append(cycle_trace)
                    break
                print(f"  [WARSTWA 4 -> DECYZJA] Wykonano akcje ewolucyjna: {cycle_trace['w4_action']}", flush=True)
                if evo_res.get("action") == "HITL" or evo_res.get("decision") == "HITL":
                    if self.interactive_gates or self.gate_approval_callback is not None:
                        return report, state.outcome(status="HITL_PAUSED", layer4=evo_res)
                    print(
                        f"  [WARSTWA 4: AUTONOMICZNA KONTYNUACJA] Agent ewolucyjny zasugerował HITL dla {failed_agent}, "
                        f"ale tryb jest nieinteraktywny (interactive_gates=False). Kontynuuję autonomiczne próby naprawy...",
                        flush=True,
                    )
                    self._record_evolution_event(
                        {
                            "type": "HITL_AUTO_BYPASS",
                            "failed_agent": failed_agent,
                            "task_id": task.get("task_id"),
                            "reason": "Non-interactive autonomous mode active",
                        }
                    )

            print(f"  [POWROT DO WARSTWY 1: REMEDIACJA] Planowanie chirurgicznej naprawy dla zadania {t_id}...", flush=True)
            remediation_errors = self._repair_cycle(
                state,
                report,
                failed_task=task,
                node_id=node_id,
                directive=remediation_directive,
                fallback_description=(
                    f"Poprzednio nie zadziałało: {issues_summary}. Zrób to: napraw węzeł {node_id} ({node_file}) i wyeliminuj błędy."
                ),
                cycle_trace=cycle_trace,
            )
            print(f"  [WARSTWA 3: RE-WERYFIKACJA] Ponowny audyt zadania {t_id} po petli W4 -> W1 -> W2...", flush=True)
            report = self._run_verification_step(task, include_docs=self.include_docs, is_final_gate=False, inject_failure=False)
            if remediation_errors:
                report["status"] = "FAIL"
                report.setdefault("issues", []).extend(remediation_errors)
                report.setdefault("errors", []).extend(remediation_errors)
            cycle_trace["w3_post_remediation_status"] = report["status"]
            state.architecture_cycles.append(cycle_trace)
            print(
                f"  [CYKL #{state.replan_count} ZAKONCZONY] W2 -> W3(FAIL) -> W4({cycle_trace['w4_action']}) -> "
                f"W1({cycle_trace['w1_remediation_task_id']}) -> W2 -> W3({report['status']})",
                flush=True,
            )
        return report, None

    def _repair_cycle(
        self,
        state: _RunState,
        report: dict[str, Any],
        failed_task: dict[str, Any],
        node_id: str,
        directive: str,
        fallback_description: str,
        extra_tasks: list[dict[str, Any]] | None = None,
        append_to_queue: bool = False,
        cycle_trace: dict[str, Any] | None = None,
    ) -> list[str]:
        """One W1 -> W2 repair shared by task repairs and the Gate 3 defense: the remediation planner proposes
        surgical tasks, each is routed to its file and built. Returns the builder errors, never swallows them."""
        blast = calculate_blast_radius(node_id, self.matrix_path)
        planner_out = self._call_agent(
            self.agents_dir / "planning" / "remediation_planner.md",
            {
                "user_prompt": state.user_prompt,
                "error_report": report,
                "failed_task": failed_task,
                "remediation_directive": directive,
                "agent_registry": read_json_state(self.registry_path),
                "blast_radius": blast,
                "hypergraph_matrix": get_scoped_hypergraph_context(self.matrix_path, blast_radius=blast),
                "include_docs": self.include_docs,
            },
            model_tier="LRM",
            provider=self.provider,
        )["output"]
        proposed = planner_out.get("surgical_tasks") or planner_out.get("tasks") or []
        surgical = [t for t in proposed if isinstance(t, dict)] if isinstance(proposed, list) else []
        for extra in extra_tasks or []:
            covers = str(extra.pop("covers", "")).lower()
            if not covers or not any(covers in str(t.get("description", "")).lower() for t in surgical):
                surgical.append(extra)
        failed_id = str(failed_task.get("task_id", "T1"))
        if not surgical:
            surgical = [
                {
                    "task_id": f"{failed_id}_FIX",
                    "target_node": node_id,
                    "assigned_agent": str(failed_task.get("assigned_agent") or ""),
                    "description": fallback_description,
                    "status": "TODO",
                }
            ]

        errors: list[str] = []
        context = str(failed_task.get("description", "")).strip()
        for stask in surgical:
            st_node, st_file = self._resolve_target_node(stask.get("target_node") or node_id, task=stask, fallback=node_id)
            stask["target_node"] = st_node
            default_agent = _default_agent(st_file)
            requested = str(stask.get("assigned_agent") or "").strip()
            # A writer is never sent to edit code; an unnamed agent gets the default for the file.
            if not requested or ("writer" in requested and not _is_document(st_file)):
                requested = default_agent
            stask["assigned_agent"] = self._resolve_active_agent(requested, fallback=default_agent)
            stask.setdefault("task_id", f"{failed_id}_FIX")
            if _is_document(st_file) and context and context[:30].lower() not in str(stask.get("description", "")).lower():
                stask["description"] = f"[Kontekst sekcji: {context}] {stask.get('description', '')}"
            if cycle_trace is not None:
                cycle_trace["w1_remediation_task_id"] = str(stask["task_id"])
            st_tier = select_model_tier(st_node, self.matrix_path)
            print(
                f"  [WARSTWA 2: BUDOWANIE NAPRAWCZE] Zadanie chirurgiczne {stask['task_id']} "
                f"[{st_file}] przez agenta '{stask['assigned_agent']}' (Tier: {st_tier})...",
                flush=True,
            )
            try:
                self._execute_builder_step(stask, model_tier=st_tier)
                self._refresh_experiment_after_code(st_node)
                stask["status"] = "DONE"
            except Exception as exc:
                err_msg = f"Wyjątek zadania naprawczego {stask.get('task_id')} na węźle {st_node} ({st_file}): {exc}"
                print(f"  [OSTRZEŻENIE: BŁĄD ZADANIA NAPRAWCZEGO] {err_msg}", flush=True)
                errors.append(err_msg)
                stask["status"] = "FAILED"
            if append_to_queue:
                state.tasks.append(stask)
                write_json_state(self.task_queue_path, state.tasks)
        return errors

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
            shown = "; ".join(_fit_items(issues)) or "Usterka obrony pracy (Gate 3)"
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
                    "assigned_agent": _default_agent(def_file),
                },
                node_id=def_node,
                directive=(
                    f"Poprzednio nie zadziałało podczas obrony Gate 3: {shown}. "
                    "Zrób to: usun usterki i doprowadz prace do pelnej zgodnosci."
                ),
                fallback_description=f"Poprzednio nie zadziałało: {shown}. Zrób to: usun bledy obrony pracy.",
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
