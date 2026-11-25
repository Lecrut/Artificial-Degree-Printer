"""Layer 3: verification of a task, factual audit of the workspace, PDF build."""

from __future__ import annotations


from typing import Any

from adk.orchestration.failure_attribution import _is_test, _pytest_culprits, _suspect_test, _traceback_culprit
from adk.orchestration import agent_texts as texts
from adk.orchestration.factual_audit import thesis_missing_chapters
from adk.core.models import ValidationReport, read_json_state, write_json_state
from adk.hypergraph import Hypergraph
from adk.tools.verification import (
    check_entrypoint_parameters,
    check_parameter_closure,
    compile_symbolic_references,
    iter_workspace_python_files,
    run_isolated_tests,
)
from adk.tools.verification.contract_check import check_import_contract
from adk.orchestration.common import (
    THESIS_FILE,
    _agent_for_path,
    _clip_log,
    _declared_vs_measured_metrics,
    _degenerate_metrics,
)
from adk.orchestration.failure_kinds import _collect_report_issues


def _task_scope(node_path: str, written: set[str], h: Hypergraph | None) -> dict[str, list[str]]:
    """Scope of an intermediate task (R4): its file, the files written since the last verification, and from H
    the tests of every module among them (T members of its I bag) and the helper files they own. The whole
    workspace is judged only at the milestones (factual audit, Gate 3); a writer's task is not judged on code."""
    candidates = {node_path, *written}
    if h is not None:
        owners = {h.owner_of(p) for p in candidates} - {None}
        candidates |= {f for v in owners for f in h.files_of(v) if f.endswith(".py")}
        candidates |= {t for v in owners for t in h.tests_of(v)}
    files = {p for p in candidates if p.endswith(".py") and not _is_test(p)}
    tests = {p for p in candidates if p.endswith(".py") and _is_test(p)}
    return {"files": sorted(files), "tests": sorted(tests)}


class VerificationMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""


    def _run_verification_step(
        self,
        current_task: dict[str, Any],
        include_docs: bool | None = None,
        is_final_gate: bool = False,
    ) -> dict[str, Any]:
        """Run Edge-Scoped Layer 3 verification tools and supervisor agents, writing state/validation_report.json."""
        effective_include_docs = self.include_docs if include_docs is None else bool(include_docs)
        h = self._project_h()
        target_node, node_path = self._resolve_target_node(
            str(current_task.get("target_node") or THESIS_FILE), task=current_task, fallback=THESIS_FILE
        )
        current_task["target_node"] = target_node
        active_edges = sorted(h.edges_of(target_node)) if h is not None and target_node in h.vertices else []

        is_doc_scope = is_final_gate or node_path.endswith((".md", ".tex"))
        is_data_scope = (not is_doc_scope) and (
            node_path.endswith(".csv") or (h is not None and h.output_producer(node_path) is not None)
        )

        self.logger.log_step(
            "VERIFICATION",
            f"Weryfikacja zadania {current_task.get('task_id')} na węźle {target_node} ({node_path})",
            {
                "active_edges": active_edges,
                "is_doc_scope": is_doc_scope,
                "is_data_scope": is_data_scope,
                "is_final_gate": is_final_gate,
                "include_docs": effective_include_docs,
            },
        )
        written = set(self._written_since_verification)
        self._written_since_verification = set()
        code_checked = is_final_gate or not is_doc_scope
        scope = _task_scope(node_path, written, h) if not is_final_gate and code_checked else None
        scope_paths = None if scope is None else set(scope["files"]) | set(scope["tests"])

        if code_checked:
            test_res = run_isolated_tests(
                self.workspace_dir,
                use_docker=False,
                verification_dir=self.adk_root / "tools" / "verification",
                scope=scope,
            )
        else:
            test_res = {
                "status": "PASS", "errors": [], "lint_warnings": [], "out_of_scope": [],
                "stdout": texts.DOC_TASK_NO_CODE_CHECK,
            }
        # Hyperedge contract (test <-> module) and the static import contract (L1: names imported from a
        # workspace module exist there, nothing executed): deterministic, precise, listed before pytest's
        # tracebacks. The declared entrypoint must not hide experiment settings in literal defaults.
        blueprint_now = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        declared_entry = str(blueprint_now.get("entrypoint") or "") if isinstance(blueprint_now, dict) else ""
        contract_violations: list[str] = []
        if code_checked:
            ws_root = self.workspace_dir.resolve()
            import_checked = (
                scope["files"]
                if scope is not None
                else [p.relative_to(ws_root).as_posix() for p in iter_workspace_python_files(self.workspace_dir) if not _is_test(p.name)]
            )
            for rel in import_checked:
                contract_violations += check_import_contract(self.workspace_dir, rel)
            if scope_paths is None or declared_entry.partition(":")[0] in scope_paths:
                contract_violations += check_entrypoint_parameters(self.workspace_dir, declared_entry or None)
        # Breaches of σ name their culprit exactly (Audit VI A5): they decide who repairs, before any heuristic.
        spec_found = (
            self._spec_violations(scope_paths)
            + self._unimplemented(None if is_final_gate else {node_path})
        ) if code_checked else []
        contract_violations += [str(v) for v in spec_found]
        if code_checked:
            test_res["errors"] = self._without_stub_failures(list(test_res.get("errors") or []))
            if not test_res["errors"]:
                test_res["status"] = "PASS"
        declared_metrics = [str(m) for m in (blueprint_now.get("metrics") or [])] if isinstance(blueprint_now, dict) else []
        metric_findings = _declared_vs_measured_metrics(declared_metrics, self.workspace_dir)
        contract_warnings = (
            check_parameter_closure(self.workspace_dir)
            + list(test_res.get("lint_warnings") or [])
            + metric_findings
            + list(test_res.get("out_of_scope") or [])
        )
        if contract_violations:
            test_res["errors"] = contract_violations + list(test_res.get("errors") or [])
            test_res["status"] = "FAIL"
        snapshot = self._collect_workspace_snapshot()
        if scope_paths is not None:
            snapshot["code_files"] = {k: v for k, v in snapshot["code_files"].items() if k in scope_paths}

        # Only attach experiment errors to tasks that govern the results: the results file itself or the entrypoint
        # module that writes it (since U5 no task targets results.csv, so the error reached no one otherwise).
        # The declared figures module (`plots`) runs after the entrypoint, so its failure is its own task's (2026-11-21,
        # 01: DATA_FAILED during R3_1 for figures.py, and the task was verified).
        declared_plots = str(blueprint_now.get("plots") or "") if isinstance(blueprint_now, dict) else ""
        governs_results = is_data_scope or any(
            declared and node_path == declared.partition(":")[0] for declared in (declared_entry, declared_plots)
        )
        if self._last_experiment_error and governs_results:
            experiment_err = _clip_log(self._last_experiment_error)
            if experiment_err not in test_res["errors"]:
                test_res["errors"].append(experiment_err)
            test_res["status"] = "FAIL"
        # The entrypoint is judged on its metrics at its own task, not only at Gate 3 (2026-11-23, 01: `mean_td_error`
        # was written as `mean_td_error_final` and two re-plan rounds went to it after everything else was verified).
        if not is_final_gate and declared_entry and node_path == declared_entry.partition(":")[0]:
            missing = [texts.metric_not_measured(m) for m in declared_metrics if texts.metric_not_measured(m) in metric_findings]
            extra = [f for f in metric_findings if f not in missing and f.endswith("not declared in the plan.")] if missing else []
            if missing or (degenerate := _degenerate_metrics(self.workspace_dir)):
                test_res["errors"] += missing + extra + (degenerate if not missing else [])
                test_res["status"] = "FAIL"

        if is_doc_scope and not is_final_gate:
            code_audit = {
                "verdict": "PASS",
                "issues": [],
                "status": "PASS",
                "skipped": "is_doc_scope",
            }
        elif not is_final_gate:
            # The findings of py_compile, the import check, ruff, pytest and the contracts are deterministic and
            # already worded for the repair; a model reading them added 41 calls and ~10 min to the 2026-11-13
            # run and nothing to the diagnosis. The LLM auditor stays for the Gate 3 review.
            code_audit = {"verdict": "PASS", "issues": [], "status": "PASS", "skipped": "deterministic_only"}
        else:
            code_audit = self._call_agent(
                self.agents_dir / "verification" / "code_auditor.md",
                {
                    "issues": test_res["errors"],
                    "test_report": test_res,
                    "code_files": snapshot["code_files"],
                },
                model_tier="SML",
                provider=self.provider,
            )["output"]

        ref_errors: list[str] = []
        symbolic_reports: dict[str, Any] = {}
        compiled_docs: dict[str, str] = {}

        if is_doc_scope:
            if effective_include_docs:
                self._ensure_fresh_results()  # Φ_R: the thesis cites results of the current code, not of an older one
                doc_files = list(self.workspace_dir.glob("*.md")) + list(self.workspace_dir.glob("*.tex"))
                for doc_file in doc_files:
                    if ".compiled." in doc_file.name:
                        continue
                    comp = compile_symbolic_references(doc_file, self.workspace_dir)
                    symbolic_reports[doc_file.name] = {
                        "status": comp["status"],
                        "errors": comp["errors"],
                        "resolved_references": comp["resolved_references"],
                        "stale_csv_files": comp["stale_csv_files"],
                    }
                    compiled_docs[doc_file.name] = comp["compiled_text"]
                    if comp["status"] == "FAIL":
                        ref_errors.extend(comp["errors"])

                
                if is_final_gate and getattr(self, "multi_cycle_waves", False):
                    md_thesis = self.workspace_dir / "thesis.md"
                    t_type_check = str(getattr(self, "planned_thesis_type", "inzynierska") or "inzynierska").strip().lower()
                    if md_thesis.exists() and t_type_check not in ("paper", "article", "scientific_paper"):
                        expected_ch = self._expected_chapters()
                        missing_ch = thesis_missing_chapters(md_thesis.read_text(encoding="utf-8", errors="ignore"), expected_ch)
                        if missing_ch:
                            ref_errors.append(texts.missing_chapters([f"Chapter {i} ({expected_ch[i]})" for i in missing_ch]))
                if not is_final_gate:
                    pending_files = self._get_pending_future_files(current_task)
                    # Placeholders (`<file>:<method>`) and wrong CSV file names (`...: no such file. The results are in
                    # results.csv`) never become valid later; fail them in the chapter that wrote them (§XXVII: 02 T1).
                    ref_errors = [
                        err for err in ref_errors
                        if not (
                            "<" not in err
                            and ": no such file. The results are in " not in err
                            and any(pf in err for pf in pending_files)
                        )
                    ]

                if is_final_gate:
                    symbolic_audit = self._call_agent(
                        self.agents_dir / "verification" / "symbolic_auditor.md",
                        {
                            "issues": ref_errors,
                            "symbolic_reports": symbolic_reports,
                            "csv_files": snapshot["csv_files"],
                            "bib_files": snapshot["bib_files"],
                        },
                        model_tier="SML",
                        provider=self.provider,
                    )["output"]
                else:
                    # The pointer compiler's findings are exact and carry their fix hints; a small model reading
                    # them only reworded them (2026-11-15: `\ref_csv{<file>}`, duplicates in every CRITIC, 26 calls).
                    symbolic_audit = {"status": "FAIL" if ref_errors else "PASS", "issues": list(ref_errors), "skipped": "deterministic_only"}
            else:
                symbolic_audit = {
                    "status": "PASS",
                    "issues": [],
                    "skipped": "include_docs=False",
                }

            if not is_final_gate:
                redteam_audit = {
                    "status": "SKIPPED_INTERMEDIATE_TASK",
                    "verdict": "PASS",
                    "gate_3_approved": False,
                    "issues": [],
                }
            else:
                redteam_audit = self._call_agent(
                    self.agents_dir / "verification" / "redteam_critic_guard.md",
                    {
                        "issues": code_audit.get("issues", []) + symbolic_audit.get("issues", []),
                        "code_audit": code_audit,
                        "symbolic_audit": symbolic_audit,
                        "code_files": snapshot["code_files"],
                        "csv_files": snapshot["csv_files"],
                        "compiled_docs": compiled_docs,
                        # The pre-registration: what the plan said it would measure, and what was measured.
                        "declared_metrics": declared_metrics,
                        "metric_registration_findings": metric_findings,
                    },
                    model_tier="LRM",
                    provider=self.provider,
                )["output"]
        else:
            symbolic_audit = {
                "status": "SKIPPED_OUT_OF_EDGE_SCOPE",
                "verdict": "PASS",
                "skipped": "SKIPPED_OUT_OF_EDGE_SCOPE",
                "issues": [],
            }
            redteam_audit = {
                "status": "SKIPPED_OUT_OF_EDGE_SCOPE",
                "verdict": "PASS",
                "skipped": "SKIPPED_OUT_OF_EDGE_SCOPE",
                "issues": [],
            }

        # §XI B0: an error is what the harness proved (pytest, ruff, σ, pointers, declared metrics); the
        # opinions of the model auditors are warnings, reported and never repaired. On 2026-11-18 the red team
        # failed all 24 defenses by rewording pytest, and every reworded copy went to the repair as work.
        opinion_warnings: list[str] = []

        def _is_supervisor_pass(sup: dict[str, Any]) -> bool:
            if is_final_gate and sup.get("gate_3_approved") is False:
                return False
            return sup.get("status") in ("PASS", "SKIPPED_OUT_OF_EDGE_SCOPE", "SKIPPED_INTERMEDIATE_TASK")

        # Enforce deterministic symbolic ground truth so small LLMs (e.g. gemma4:e2b) cannot ignore
        # real pytest/ruff/ref_compiler errors OR hallucinate failures when all deterministic checks pass.
        # The approval of the defense is the red team's alone, counted by the harness below; a field of that name in an
        # answer of the other auditors is nobody's decision (`_is_supervisor_pass` would read it as a veto).
        for audit in (code_audit, symbolic_audit):
            audit.pop("gate_3_approved", None)
        deterministic_code_fail = bool(
            test_res.get("status") == "FAIL" or test_res.get("errors")
        )
        if deterministic_code_fail:
            code_audit["status"] = "FAIL"
            # The errors are pytest's, ruff's and the contracts'; the model auditor's issues become warnings.
            real_errors = list(dict.fromkeys(str(err) for err in (test_res.get("errors") or [])))
            opinion_warnings += [str(i) for i in (code_audit.get("issues") or []) if str(i) not in real_errors]
            code_audit["issues"] = real_errors or [texts.contract_mismatch(current_task.get("task_id"), target_node)]
        elif code_audit.get("status") != "PASS":
            opinion_warnings += [str(i) for i in (code_audit.get("issues") or [])]
            code_audit["status"] = "PASS"
            code_audit["issues"] = []

        if is_doc_scope:
            deterministic_doc_fail = bool(ref_errors)
            if deterministic_doc_fail:
                symbolic_audit["status"] = "FAIL"
                # The errors are the pointer compiler's; the model auditor's issues become warnings.
                opinion_warnings += [str(i) for i in (symbolic_audit.get("issues") or []) if str(i) not in ref_errors]
                symbolic_audit["issues"] = list(ref_errors) or [texts.pointer_mismatch(current_task.get("task_id"), target_node)]
            elif effective_include_docs:
                opinion_warnings += [str(i) for i in (symbolic_audit.get("issues") or [])]
                symbolic_audit["status"] = "PASS"
                symbolic_audit["issues"] = []

        # Only a declared metric that was never measured blocks; a measured extra one is a warning (it was blocking
        # too, against the docstring of `_declared_vs_measured_metrics`).
        unmeasured = {texts.metric_not_measured(m) for m in declared_metrics}
        metric_errors = [f for f in metric_findings if f in unmeasured] if is_final_gate else []
        if is_final_gate:
            # The red team's own findings are warnings; the defense is blocked by code, pointers (above) and by
            # metrics declared in the plan that the results do not contain (counted by the harness).
            opinion_warnings += [str(i) for i in (redteam_audit.get("issues") or [])]
            redteam_audit["issues"] = metric_errors
            redteam_audit["status"] = "FAIL" if metric_errors else "PASS"
            redteam_audit["gate_3_approved"] = not metric_errors

        overall_pass = (
            _is_supervisor_pass(code_audit)
            and _is_supervisor_pass(symbolic_audit)
            and _is_supervisor_pass(redteam_audit)
        )

        # The failed file is the one the findings name (R4 pt 3), and the blamed agent is its author (R5).
        failed_file = None
        failed_agent = None
        if not overall_pass:
            failed_file = next((v.culprit for v in spec_found if v.culprit), None)
            for issue in [] if failed_file else code_audit.get("issues", []):
                for culprit, is_code in _pytest_culprits(str(issue)):
                    if is_code and _is_test(culprit):
                        # Wrong result seen only in the test frame: the unverified one of the pair. A module verified
                        # against σ and a fresh test → the test (§XIV Q2: 01 blamed ttt_agent.py for `0.1 > 0.5`);
                        # otherwise the module under test (the producer of the I bag the test belongs to in H).
                        module = h.tested_module(culprit) if h is not None else None
                        if not (module and _suspect_test(h, module, culprit)):
                            culprit = module or (node_path if not _is_test(node_path) else culprit)
                    failed_file = culprit
                    break
                if failed_file:
                    break
            if failed_file is None and self._last_experiment_error and governs_results:
                failed_file = _traceback_culprit(self._last_experiment_error, self.workspace_dir)
            if failed_file is None:
                # Pointer findings name the code file a pointer aims at, but the pointer is the writer's (X6).
                named = [
                    p
                    for issue in [*code_audit.get("issues", []), *contract_violations]
                    for p in self._workspace_paths_in(str(issue))
                ]
                failed_file = next((p for p in named if scope_paths is None or p in scope_paths), None)
                if failed_file is None and metric_errors and _is_supervisor_pass(code_audit) and _is_supervisor_pass(symbolic_audit):
                    failed_file = declared_entry.partition(":")[0] or None  # results lack a metric: the experiment's
                if failed_file is None and is_final_gate and _is_supervisor_pass(code_audit) and not _is_supervisor_pass(symbolic_audit):
                    # A finding about the document (missing chapters, pointers) is the thesis's, not the code of the task
                    # the gate happens to follow (2026-11-21, 01: figures.py was marked failed for missing chapters).
                    failed_file = THESIS_FILE
                failed_file = failed_file or node_path
            owner = h.owner_of(str(failed_file)) if h is not None else None
            author = h.vertices[owner].last_writer if owner is not None else None
            failed_agent = (author or {}).get("agent") or current_task.get("assigned_agent")
            if failed_agent == "harness":  # the harness wrote the stubs; the file's work belongs to its owner
                failed_agent = _agent_for_path(str(failed_file))

        report = ValidationReport(
            status="PASS" if overall_pass else "FAIL",
            failed_task_id=None if overall_pass else current_task.get("task_id"),
            failed_node=None if overall_pass else target_node,
            failed_file=failed_file,
            failed_agent=failed_agent,
            supervisors={
                "code_auditor": code_audit,
                "symbolic_auditor": symbolic_audit,
                "redteam_critic_guard": redteam_audit,
            },
            summary="All Layer 3 gates passed." if overall_pass else "Layer 3 verification failed.",
        ).to_dict()
        if contract_violations and not overall_pass:
            report["contract_violations"] = contract_violations
        # Non-blocking findings (closure of declared parameters, mechanical lint, opinions of the model auditors):
        # reported, never repaired.
        warnings = list(dict.fromkeys([*contract_warnings, *opinion_warnings]))
        if warnings:
            report["warnings"] = warnings[:20]

        write_json_state(self.validation_report_path, report)
        issues = _collect_report_issues(report)  # the findings live in the supervisors' sections, not at the top
        if not overall_pass:
            self._remember_verdict(
                (h.owner_of(str(failed_file)) if h is not None and failed_file else None) or failed_file,
                current_task.get("task_id"), issues,
            )
        self.logger.log_event(
            "VERDICT", task_id=current_task.get("task_id"), node=target_node, status=report.get("status"),
            failed_file=failed_file, failed_agent=failed_agent, first_issue=str(issues[0])[:400] if issues else None,
            errors=len(issues) if not overall_pass else 0, warnings=len(warnings),
        )
        return report


