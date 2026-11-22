"""Repair of a failed task: fast fixes by the file's author, then one pattern-gated evolution step and one planner cycle."""

from __future__ import annotations

from typing import Any

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state, write_json_state
from adk.tools.planning import select_model_tier
from adk.orchestration.findings import focus_symbols, repair_findings, symbol_sources
from adk.orchestration.import_hints import importable_names
from adk.orchestration.failure_attribution import _is_test, _suspect_test
from adk.orchestration.common import (
    _agent_for_path,
    available_package_imports,
    FAST_REPAIR_ATTEMPTS,
    _fit_items,
    _is_document,
    _RunState,
)
from adk.orchestration.plan_change import _spec_findings
from adk.orchestration.failure_kinds import (
    _issue_signature,
    _issue_category,
    HARNESS_ENFORCED_CATEGORIES,
    UNCLASSIFIED_CATEGORY,
    _collect_report_issues,
)


class RepairMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _repair_task(
        self,
        state: _RunState,
        task: dict[str, Any],
        report: dict[str, Any],
        node_id: str,
        node_file: str,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """W3(FAIL) -> fast fix by the file's author (twice, no W4/W1) -> one W4 (pattern-gated) -> W1 -> W2 -> W3.
        A task that is still failing after that is left as a gap; the queue moves on (Audit IV §IV.7 pkt 6)."""
        t_id = str(task.get("task_id", "T1"))
        t_desc = str(task.get("description", texts.NO_DESCRIPTION))
        task["repair_attempts"] = 0
        while report["status"] != "PASS" and task["repair_attempts"] < state.max_retries:
            task["status"] = "FAILED"
            write_json_state(self.task_queue_path, state.tasks)
            task["repair_attempts"] += 1
            attempt = int(task["repair_attempts"])
            state.replan_count += 1

            # The author of the file named in the findings (node `last_writer`), not the agent of this task:
            # a coder's task failing on a wrong test must discipline the tester (R5).
            failed_agent = str(report.get("failed_agent") or task.get("assigned_agent", "seed_coder"))
            failed_file = str(report.get("failed_file") or node_file)
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
            print(f"  [WARSTWA 3 -> BLAD] Wykryto usterke w zadaniu {t_id} na wezle {node_id} ({node_file})!", flush=True)

            issues_list = _collect_report_issues(report)
            issues_summary = "; ".join(_fit_items(issues_list)) if issues_list else "Usterka weryfikacji warstwy 3"
            category = _issue_category(issues_list)
            hits = state.category_hits.setdefault((failed_agent, category), {})
            hits.setdefault(t_id, (issues_list[0] if issues_list else issues_summary)[:400])
            self._log_failure_category(state.replan_count, failed_agent, category, t_id)
            # The findings travel once, in the report. Repeating them here doubled the planner's and the
            # architect's input (2026-11-12: ~46k characters per call, 87-90% of it two copies of pytest output).
            remediation_directive = texts.remediation_directive(t_id, node_id, node_file)

            if attempt <= FAST_REPAIR_ATTEMPTS:
                # Fast path: the findings are deterministic and self-describing (syntax, import, ruff, pytest,
                # contracts), so the author of the failed file gets them verbatim, right away, with no planner
                # and no evolution in between. 2026-11-13: that detour cost ~1.5 min per failure.
                # A derived artifact (CSV, figure) is repaired through its producer: on 2026-11-14 agents were
                # sent to "fix" figures/comparison.pdf and results.csv, files no one can edit.
                fast_target = self._repair_target(failed_file)
                h = self._project_h()
                if fast_target != failed_file:
                    owner = h.owner_of(fast_target) if h is not None else None
                    author = h.vertices[owner].last_writer if owner is not None else None
                    failed_agent = str((author or {}).get("agent") or _agent_for_path(fast_target))
                # Controlled change of the plan (Audit VII B4): the same breach of σ again on the same vertex means
                # the specification may be what is wrong. The
                # planner decides before the next attempt: amend the interface, or keep it and the coder goes on.
                self._amend_spec_if_wrong(failed_file, issues_list, t_id)
                # The repair names the symbols to change and each error with its line of code (§XI B1-B2): on
                # 2026-11-18 three repairs of config.py changed other symbols than the one with the error.
                findings = repair_findings(issues_list, self.workspace_dir, lambda rel: importable_names(h, rel, available_package_imports()))
                focus = focus_symbols(findings, fast_target)
                notes = [str(f) for f in findings]
                module = h.tested_module(fast_target) if h is not None and _is_test(fast_target) else None
                if module and _suspect_test(h, module, fast_target):
                    notes.insert(0, texts.test_contradicts_verified_module(module))  # §XIV Q2
                fast_task = {
                    **task,
                    "repair_of": t_id,
                    "task_id": f"{t_id}_FIX{attempt}",
                    "target_node": fast_target,
                    "assigned_agent": failed_agent,
                    "description": texts.focused_repair_description(fast_target, focus, _fit_items(notes)),
                    "task_context": t_desc,
                }
                fast_task.pop("repair_focus", None)
                if focus:
                    fast_task["repair_focus"] = {"file": fast_target, "symbols": symbol_sources(self.workspace_dir, fast_target, focus)}
                # The model follows the vertex, not the attempt number: before, the large model could never take
                # over a fast repair (2026-11-18: 139 of 142 coder calls on the small model).
                fast_tier = select_model_tier(failures=self._vertex_failures(fast_target))
                print(
                    f"  [WARSTWA 2: SZYBKA NAPRAWA {attempt}/{FAST_REPAIR_ATTEMPTS}] {fast_target} przez '{failed_agent}' "
                    f"(Tier: {fast_tier}), bez W4/W1...",
                    flush=True,
                )
                builder_error: str | None = None
                signature_before = _issue_signature({"issues": issues_list})
                try:
                    self._execute_builder_step(fast_task, model_tier=fast_tier)
                    self._refresh_experiment_after_code(node_id)
                except Exception as exc:
                    # A crashed repair must not look like a completed one: keep it on record.
                    builder_error = texts.fast_repair_exception(fast_task["task_id"], fast_target, exc)
                    print(f"  [OSTRZEŻENIE: BŁĄD SZYBKIEJ NAPRAWY] {builder_error}", flush=True)
                    cycle_trace["builder_error"] = str(exc)
                report = self._run_verification_step(task, include_docs=self.include_docs, is_final_gate=False)
                if builder_error:
                    report["status"] = "FAIL"
                    report["failed_agent"] = report.get("failed_agent") or failed_agent
                    report.setdefault("issues", []).append(builder_error)
                    report.setdefault("errors", []).append(builder_error)
                if report["status"] != "PASS" and signature_before and (
                    _issue_signature({"issues": _collect_report_issues(report)}) == signature_before
                ) and not _spec_findings(_collect_report_issues(report)):
                    # §XIV Q3: the same error after the author's repair (01: T1 and T2 three times each) — this
                    # author will not fix it here; go straight to the full cycle (repair planner) instead. Not for a
                    # breach of σ: the next attempt first lets the planner judge the interface (`_amend_spec_if_wrong`),
                    # which the shortcut used to skip.
                    self.logger.log_event("REPAIR_SAME_ERROR", task_id=t_id, target=fast_target, attempt=attempt)
                    task["repair_attempts"] = max(int(task["repair_attempts"]), FAST_REPAIR_ATTEMPTS)
                cycle_trace["w4_action"] = "FAST_FIX"
                cycle_trace["w1_remediation_task_id"] = fast_task["task_id"]
                cycle_trace["w3_post_remediation_status"] = report["status"]
                state.architecture_cycles.append(cycle_trace)
                continue

            # One full cycle. W4 only for a pattern: the same category of failure of the same agent in at least
            # two different tasks, never for what the harness itself enforces, and once per (agent, category).
            # (The environment is fixed, D1: a missing package is an L1 finding, never an evolution matter.)
            evo_key = (failed_agent, category)
            pattern = len(hits) >= 2
            run_evolution = False
            if not self.enable_layer4:
                pass
            elif evo_key in state.seen_evo:
                cycle_trace["w4_action"] = "SKIPPED_SAME_FAILURE"
                print("  [WARSTWA 4: POMINIĘTA] Ta kategoria błędu tego agenta ma już regułę w tym przebiegu.", flush=True)
                state.repeats_after_evolution[evo_key] = state.repeats_after_evolution.get(evo_key, 0) + 1
                if state.repeats_after_evolution[evo_key] >= 2:
                    # The prompt was already changed for exactly this kind of failure and it is still here: the
                    # defect is not in the agent. Stop spending retries on it and say where to look instead.
                    task["harness_bug"] = self._report_harness_bug(_issue_signature({"issues": issues_list}), t_id)
                    cycle_trace["w4_action"] = "REPORT_HARNESS_BUG"
                    state.architecture_cycles.append(cycle_trace)
                    break
            elif category in HARNESS_ENFORCED_CATEGORIES:
                cycle_trace["w4_action"] = "SKIPPED_HARNESS_ENFORCED"
                print(f"  [WARSTWA 4: POMINIĘTA] Kategorię '{category}' egzekwuje harness; reguła promptu nic tu nie da.", flush=True)
            elif category == UNCLASSIFIED_CATEGORY:
                cycle_trace["w4_action"] = "SKIPPED_UNCLASSIFIED"
                print("  [WARSTWA 4: POMINIĘTA] Nierozpoznany rodzaj błędu; różne porażki to jeszcze nie wzorzec.", flush=True)
            elif not pattern:
                cycle_trace["w4_action"] = "SKIPPED_NO_PATTERN"
                print(f"  [WARSTWA 4: POMINIĘTA] Kategoria '{category}' wystąpiła dotąd w jednym zadaniu; ewolucja czeka na wzorzec.", flush=True)
            else:
                run_evolution = True
                state.seen_evo.add(evo_key)

            if run_evolution:
                print(
                    f"  [WARSTWA 4: SAMOEWOLUCJA] Uruchomienie Architekta Ewolucji (cykl #{state.replan_count}, agent: {failed_agent}, "
                    f"kategoria: {category} w {len(hits)} zadaniach)...",
                    flush=True,
                )
                evo_res = self._run_evolution_step(
                    {
                        # The architect sees the pattern (several incidents, different files), not one report.
                        "pattern": {
                            "category": category,
                            "occurrences": len(hits),
                            "tasks": sorted(hits),
                            "examples": list(hits.values())[:3],
                        },
                        "validation_report": {
                            "status": "FAIL",
                            "failed_file": failed_file,
                            "failed_agent": failed_agent,
                            "issues": _fit_items(issues_list)[:3],
                        },
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

            h = self._project_h()
            if h is not None and failed_file in h.vertices:
                # O7 (Audit VI A9): the oracle named the culprit and its author already had the local attempts; a
                # planner's prose diagnosis of a known fault cost ~30% of the LLM time (T2). The vertex keeps its
                # history and comes back in the next generation.
                cycle_trace["w1_remediation_task_id"] = "SKIPPED_CULPRIT_KNOWN"
                state.architecture_cycles.append(cycle_trace)
                self.logger.log_event("REMEDIATION_SKIPPED", task_id=t_id, culprit=failed_file)
                break
            print(f"  [POWROT DO WARSTWY 1: REMEDIACJA] Planowanie chirurgicznej naprawy dla zadania {t_id}...", flush=True)
            remediation_errors = self._repair_cycle(
                state,
                report,
                failed_task=task,
                node_id=node_id,
                directive=remediation_directive,
                fallback_description=texts.previous_attempt_failed(issues_summary, node_id, node_file),
                cycle_trace=cycle_trace,
            )
            print(f"  [WARSTWA 3: RE-WERYFIKACJA] Ponowny audyt zadania {t_id} po petli W4 -> W1 -> W2...", flush=True)
            report = self._run_verification_step(task, include_docs=self.include_docs, is_final_gate=False)
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
            # One planner cycle per task. A task that still fails is a gap in the delivery, listed in the thesis;
            # 2026-11-13 spent 35 cycles on one task and never got past it.
            break
        return report, None

    def _log_failure_category(self, cycle: int, agent: str, category: str, task_id: str) -> None:
        """Append one failure to `failure_ledger.json[category_log]`: the data the prompt consolidation uses to
        tell whether a learned rule lowered the frequency of the failures it was written for (§IV.6.3 D)."""
        ledger = read_json_state(self.failure_ledger_path) if self.failure_ledger_path.exists() else {"failures": []}
        ledger.setdefault("category_log", []).append(
            {"cycle": cycle, "agent": agent, "category": category, "task_id": task_id}
        )
        write_json_state(self.failure_ledger_path, ledger)

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
        planner_out = self._call_agent(
            self.agents_dir / "planning" / "remediation_planner.md",
            {
                "user_prompt": state.user_prompt,
                # The fields the planner acts on; the full report (supervisor dumps, every warning) averaged
                # ~13k characters per call on 2026-11-13 and repeated the same findings several times.
                "error_report": {
                    "status": report.get("status"),
                    "failed_task_id": report.get("failed_task_id"),
                    "failed_node": report.get("failed_node"),
                    "failed_file": report.get("failed_file"),
                    "failed_agent": report.get("failed_agent"),
                    "issues": _fit_items(list(dict.fromkeys(_collect_report_issues(report)))),
                    "contract_violations": report.get("contract_violations") or [],
                    "warnings": list(report.get("warnings") or [])[:5],
                },
                "failed_task": failed_task,
                "remediation_directive": directive,
                "agent_registry": read_json_state(self.registry_path),
                # The bags of the failed vertex (members, roles, states, σ): where a fix may go and what it touches.
                "hypergraph": self._h_slice(self._task_vertex(failed_task)),
                "include_docs": self.include_docs,
                # Without the signatures the planner dictated new APIs in prose (2026-11-12); σ tells it which side
                # of a test/module mismatch departs from the planned interface.
                "specification": self._specification_symbols(),
            },
            # The planner runs after the fast fixes failed, i.e. at the escalation point: the large model.
            model_tier=select_model_tier(failures=int(failed_task.get("repair_attempts", 0))),
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
            default_agent = _agent_for_path(st_file)
            requested = str(stask.get("assigned_agent") or "").strip()
            # A writer is never sent to edit code; an unnamed agent gets the default for the file.
            if not requested or ("writer" in requested and not _is_document(st_file)):
                requested = default_agent
            stask["assigned_agent"] = self._resolve_active_agent(requested, fallback=default_agent)
            stask.setdefault("task_id", f"{failed_id}_FIX")
            stask["repair_of"] = failed_id
            if _is_document(st_file) and context and context[:30].lower() not in str(stask.get("description", "")).lower():
                stask["description"] = texts.section_context(context, str(stask.get("description", "")))
            if cycle_trace is not None:
                cycle_trace["w1_remediation_task_id"] = str(stask["task_id"])
            st_tier = select_model_tier(failures=self._vertex_failures(st_file))
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
                err_msg = texts.repair_task_exception(stask.get("task_id"), st_node, st_file, exc)
                print(f"  [OSTRZEŻENIE: BŁĄD ZADANIA NAPRAWCZEGO] {err_msg}", flush=True)
                errors.append(err_msg)
                stask["status"] = "FAILED"
            if append_to_queue:
                state.tasks.append(stask)
                write_json_state(self.task_queue_path, state.tasks)
        return errors
