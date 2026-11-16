"""Layer 3: verification of a task, factual audit of the workspace, PDF build."""

from __future__ import annotations


from typing import Any

from adk.orchestration.failure_attribution import _is_test, _pytest_culprits
from adk.orchestration import agent_texts as texts
from adk.orchestration.factual_audit import thesis_missing_chapters
from adk.core.models import ValidationReport, read_json_state, write_json_state
from adk.tools.building import (
    sync_hypergraph_matrix,
)
from adk.tools.verification import (
    check_entrypoint_parameters,
    check_parameter_closure,
    check_test_contract,
    compile_symbolic_references,
    iter_workspace_python_files,
    run_isolated_tests,
)
from adk.tools.verification.contract_check import check_import_contract
from adk.orchestration.common import (
    _clip_log,
    _declared_vs_measured_metrics,
)


def _task_scope(node_path: str, written: set[str], matrix_data: dict[str, Any]) -> dict[str, list[str]]:
    """Scope of an intermediate task (R4): its node, the files written since the last verification and the tests
    coupled to them by a hyperedge. The whole workspace is judged only at the milestones (factual audit, Gate 3);
    a writer's task is not judged on code at all."""
    candidates = {node_path, *written}
    files = {p for p in candidates if p.endswith(".py") and not _is_test(p)}
    tests = {p for p in candidates if _is_test(p)}
    nodes = matrix_data.get("nodes", {})
    by_path = {str(m.get("path", "")): n_id for n_id, m in nodes.items()}
    scope_ids = {by_path[p] for p in files | tests if p in by_path}
    for members in matrix_data.get("edges", {}).values():
        if scope_ids & set(members):
            tests.update(p for p in (str(nodes.get(m, {}).get("path", "")) for m in members) if _is_test(p))
    return {"files": sorted(files), "tests": sorted(tests)}


class VerificationMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""


    def _run_verification_step(
        self,
        current_task: dict[str, Any],
        include_docs: bool | None = None,
        is_final_gate: bool = False,
        inject_failure: bool = False,
    ) -> dict[str, Any]:
        """Run Edge-Scoped Layer 3 verification tools and supervisor agents, writing state/validation_report.json."""
        effective_include_docs = self.include_docs if include_docs is None else bool(include_docs)
        if self.workspace_dir.exists():
            sync_hypergraph_matrix(self.workspace_dir, self.matrix_path)
        matrix_data = read_json_state(self.matrix_path)
        matrix_inc: dict[str, dict[str, int]] = matrix_data.get("matrix", {})

        raw_target_node = str(current_task.get("target_node", "v1"))
        target_node, node_path = self._resolve_target_node(raw_target_node, task=current_task, fallback="v1")
        current_task["target_node"] = target_node
        active_edges = [e_id for e_id, val in matrix_inc.get(target_node, {}).items() if int(val) == 1]

        is_doc_scope = is_final_gate or node_path.endswith((".md", ".tex"))
        node_kind = str(matrix_data.get("nodes", {}).get(target_node, {}).get("kind", ""))
        is_data_scope = (not is_doc_scope) and (node_path.endswith(".csv") or node_kind == "derived")

        self.logger.log_step(
            "VERIFICATION",
            f"Weryfikacja zadania {current_task.get('task_id')} na węźle {target_node} ({node_path})",
            {
                "active_edges": active_edges,
                "is_doc_scope": is_doc_scope,
                "is_data_scope": is_data_scope,
                "is_final_gate": is_final_gate,
                "include_docs": effective_include_docs,
                "inject_failure": inject_failure,
            },
        )
        written = set(self._written_since_verification)
        self._written_since_verification = set()
        code_checked = is_final_gate or not is_doc_scope
        scope = _task_scope(node_path, written, matrix_data) if not is_final_gate and code_checked else None
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
            contract_violations += check_test_contract(self.workspace_dir, self.matrix_path, only_paths=scope_paths)
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
        governs_results = is_data_scope or (bool(declared_entry) and node_path == declared_entry.partition(":")[0])
        if self._last_experiment_error and governs_results:
            experiment_err = _clip_log(self._last_experiment_error)
            if experiment_err not in test_res["errors"]:
                test_res["errors"].append(experiment_err)
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
                    "force_fail": inject_failure,
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
                        missing_ch = thesis_missing_chapters(md_thesis.read_text(encoding="utf-8", errors="ignore"))
                        if missing_ch:
                            ref_errors.append(texts.missing_chapters([texts.CHAPTER_LABELS.get(i, f"Chapter {i}") for i in missing_ch]))
                if not is_final_gate:
                    pending_files = self._get_pending_future_files(current_task)
                    ref_errors = [
                        err for err in ref_errors
                        if not any(pf in err for pf in pending_files)
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

        def _is_supervisor_pass(sup: dict[str, Any]) -> bool:
            if is_final_gate and sup.get("gate_3_approved") is False:
                return False
            return sup.get("status") in ("PASS", "SKIPPED_OUT_OF_EDGE_SCOPE", "SKIPPED_INTERMEDIATE_TASK")

        # Enforce deterministic symbolic ground truth so small LLMs (e.g. gemma4:e2b) cannot ignore
        # real pytest/ruff/ref_compiler errors OR hallucinate failures when all deterministic checks pass.
        deterministic_code_fail = bool(
            inject_failure or test_res.get("status") == "FAIL" or test_res.get("errors")
        )
        if deterministic_code_fail:
            code_audit["status"] = "FAIL"
            # Real pytest/ruff errors always come first; the LLM's issues only supplement them.
            real_errors = list(dict.fromkeys(str(err) for err in (test_res.get("errors") or [])))
            llm_issues = [str(i) for i in (code_audit.get("issues") or []) if str(i) not in real_errors]
            code_audit["issues"] = real_errors + llm_issues or [
                texts.contract_mismatch(current_task.get("task_id"), target_node)
            ]
        elif code_audit.get("status") != "PASS":
            code_audit["status"] = "PASS"
            code_audit["issues"] = []

        if is_doc_scope:
            deterministic_doc_fail = bool(inject_failure or ref_errors)
            if deterministic_doc_fail:
                symbolic_audit["status"] = "FAIL"
                # The compiler's findings always come first; the model's issues only supplement them.
                model_issues = [str(i) for i in (symbolic_audit.get("issues") or []) if str(i) not in ref_errors]
                symbolic_audit["issues"] = list(ref_errors) + model_issues or [
                    texts.pointer_mismatch(current_task.get("task_id"), target_node)
                ]
                if is_final_gate:
                    redteam_audit["status"] = "FAIL"
                    if not redteam_audit.get("issues"):
                        redteam_audit["issues"] = list(symbolic_audit["issues"])
            else:
                if effective_include_docs and not symbolic_audit.get("issues"):
                    symbolic_audit["status"] = "PASS"
                    symbolic_audit["issues"] = []
                if is_final_gate:
                    # Preserve real adversarial critique from redteam_critic_guard (Gate 3)
                    if redteam_audit.get("issues") or redteam_audit.get("gate_3_approved") is False:
                        redteam_audit["status"] = "FAIL"
                    elif not deterministic_code_fail and not redteam_audit.get("issues"):
                        redteam_audit["status"] = "PASS"

        overall_pass = (
            _is_supervisor_pass(code_audit)
            and _is_supervisor_pass(symbolic_audit)
            and _is_supervisor_pass(redteam_audit)
        )

        # The failed file is the one the findings name (R4 pt 3), and the blamed agent is its author (R5).
        failed_file = None
        failed_agent = None
        if not overall_pass:
            nodes_all = matrix_data.get("nodes", {})
            for issue in code_audit.get("issues", []):
                for culprit, is_code in _pytest_culprits(str(issue)):
                    if is_code and _is_test(culprit):
                        # Wrong result seen only in the test frame: the module under test, i.e. a code module
                        # coupled to the test by a hyperedge (in scope first).
                        by_path = {str(m.get("path", "")): n for n, m in nodes_all.items()}
                        test_id = by_path.get(culprit)
                        coupled = [
                            str(nodes_all.get(m, {}).get("path", ""))
                            for members in matrix_data.get("edges", {}).values()
                            if test_id in members
                            for m in members
                        ]
                        modules = [p for p in coupled if p.endswith(".py") and not _is_test(p)]
                        modules.sort(key=lambda p: scope_paths is not None and p not in scope_paths)
                        culprit = modules[0] if modules else (node_path if not _is_test(node_path) else culprit)
                    failed_file = culprit
                    break
                if failed_file:
                    break
            if failed_file is None:
                named = [
                    p
                    for issue in [*code_audit.get("issues", []), *ref_errors, *contract_violations]
                    for p in self._workspace_paths_in(str(issue))
                ]
                failed_file = next((p for p in named if scope_paths is None or p in scope_paths), None) or node_path
            author = next((m.get("last_writer") for m in nodes_all.values() if str(m.get("path", "")) == failed_file), None)
            failed_agent = (author or {}).get("agent") or current_task.get("assigned_agent")

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
        # Non-blocking findings (closure of declared parameters, lint left after `ruff --fix`): reported, not repaired.
        if contract_warnings:
            report["warnings"] = list(dict.fromkeys(contract_warnings))[:12]

        write_json_state(self.validation_report_path, report)
        return report


