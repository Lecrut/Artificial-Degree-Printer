"""Layer 3: verification of a task, factual audit of the workspace, PDF build."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any

from adk.core.models import ValidationReport, read_json_state, write_json_state
from adk.tools.building import (
    sync_hypergraph_matrix,
)
from adk.tools.verification import (
    check_entrypoint_parameters,
    check_parameter_closure,
    check_test_contract,
    compile_symbolic_references,
    run_isolated_tests,
)
from adk.orchestration.common import (
    _collect_report_issues,
    _fit_items,
    _clip_log,
    _declared_vs_measured_metrics,
)


class VerificationMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _get_pending_future_files(self, current_task: dict[str, Any]) -> set[str]:
        """Return filenames scheduled to be created by subsequent TODO tasks in the queue."""
        pending: set[str] = set()
        if not self.task_queue_path.exists():
            return pending
        tasks = read_json_state(self.task_queue_path)
        if not isinstance(tasks, list):
            return pending

        current_id = str(current_task.get("task_id", ""))
        found_current = False
        matrix_data = read_json_state(self.matrix_path)
        matrix_nodes = matrix_data.get("nodes", {})

        for t in tasks:
            if not isinstance(t, dict):
                continue
            t_id = str(t.get("task_id", ""))
            if t_id == current_id:
                found_current = True
                continue
            if found_current and t.get("status") == "TODO":
                t_node = str(t.get("target_node", ""))
                node_meta = matrix_nodes.get(t_node, {})
                path_str = str(node_meta.get("path", ""))
                if path_str:
                    pending.add(Path(path_str).name)
                    pending.add(path_str)
                role = self._role_of(t_node)
                if role in ("config", "core"):
                    pending.update({self._role_file("config"), self._role_file("core")})
                elif role in ("results", "tests"):
                    pending.update({self._role_file("results"), "figures", "plot_results.py", self._role_file("tests")})
        return pending

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
        test_res = run_isolated_tests(
            self.workspace_dir,
            use_docker=False,
            verification_dir=self.adk_root / "tools" / "verification",
        )
        # Hyperedge contract (test <-> module): deterministic, precise, and listed before pytest's tracebacks.
        # The declared entrypoint must not hide experiment settings in literal defaults.
        blueprint_now = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        declared_entry = str(blueprint_now.get("entrypoint") or "") if isinstance(blueprint_now, dict) else ""
        contract_violations = check_test_contract(self.workspace_dir, self.matrix_path) + check_entrypoint_parameters(
            self.workspace_dir, declared_entry or None
        )
        declared_metrics = [str(m) for m in (blueprint_now.get("metrics") or [])] if isinstance(blueprint_now, dict) else []
        metric_findings = _declared_vs_measured_metrics(declared_metrics, self.workspace_dir)
        contract_warnings = (
            check_parameter_closure(self.workspace_dir) + list(test_res.get("lint_warnings") or []) + metric_findings
        )
        if contract_violations:
            test_res["errors"] = contract_violations + list(test_res.get("errors") or [])
            test_res["status"] = "FAIL"
        snapshot = self._collect_workspace_snapshot()

        # Only attach experiment errors to tasks that actually govern experiments/data (e.g. results.csv)
        if self._last_experiment_error and is_data_scope:
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
                    if md_thesis.exists():
                        raw_th = md_thesis.read_text(encoding="utf-8", errors="ignore")
                        found_ch_nums = set()
                        for m in re.finditer(r"^##\s+([^\n]+)", raw_th, flags=re.MULTILINE):
                            h_line = m.group(1).lower()
                            m_num = re.search(r"(?:rozdzia[łl]|chapter)\s+(\d+)", h_line)
                            if m_num:
                                found_ch_nums.add(int(m_num.group(1)))
                            elif any(w in h_line for w in ("wstęp", "wstep", "cel", "teza", "intro", "problem")):
                                found_ch_nums.add(1)
                            elif any(w in h_line for w in ("sota", "stan wiedzy", "literatur", "przegląd", "przeglad", "related", "background")):
                                found_ch_nums.add(2)
                            elif any(w in h_line for w in ("architektur", "formalizm", "matematyczn", "system", "design", "model")):
                                found_ch_nums.add(3)
                            elif any(w in h_line for w in ("implementacj", "algorytm", "struktury", "implementation")):
                                found_ch_nums.add(4)
                            elif any(w in h_line for w in ("wyniki", "ewaluacj", "eksperyment", "badani", "evaluation", "metodologia", "empirical", "results")):
                                found_ch_nums.add(5)
                            elif any(w in h_line for w in ("podsumowan", "wnioski", "conclusi", "kierunki", "summary")):
                                found_ch_nums.add(6)

                        t_type_check = str(getattr(self, "planned_thesis_type", "inzynierska") or "inzynierska").strip().lower()
                        if t_type_check not in ("paper", "article", "scientific_paper"):
                            missing_ch = [i for i in range(1, 7) if i not in found_ch_nums]
                            if missing_ch:
                                ch_names = {
                                    1: "Rozdział 1 (Wstęp i Teza)",
                                    2: "Rozdział 2 (Stan Wiedzy / SOTA)",
                                    3: "Rozdział 3 (Architektura i Formalizm)",
                                    4: "Rozdział 4 (Implementacja AST)",
                                    5: "Rozdział 5 (Badania Eksperymentalne)",
                                    6: "Rozdział 6 (Podsumowanie i Wnioski)",
                                }
                                missing_labels = [ch_names.get(i, f"Rozdział {i}") for i in missing_ch]
                                missing_msg = f"Niekompletna praca dyplomowa: brakujące rozdziały w thesis.md: {missing_labels}. Wymagane jest pełne 6 rozdziałów."
                                ref_errors.append(missing_msg)
                if not is_final_gate:
                    pending_files = self._get_pending_future_files(current_task)
                    ref_errors = [
                        err for err in ref_errors
                        if not any(pf in err for pf in pending_files)
                    ]

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
            real_errors = [str(err) for err in (test_res.get("errors") or [])]
            llm_issues = [str(i) for i in (code_audit.get("issues") or []) if str(i) not in real_errors]
            code_audit["issues"] = real_errors + llm_issues or [
                f"Wykryto niezgodność kontraktu w zadaniu {current_task.get('task_id')} na węźle {target_node} (wymagana pętla W3 -> W4 -> W1 -> W2)."
            ]
        elif code_audit.get("status") != "PASS":
            code_audit["status"] = "PASS"
            code_audit["issues"] = []

        if is_doc_scope:
            deterministic_doc_fail = bool(inject_failure or ref_errors)
            if deterministic_doc_fail:
                symbolic_audit["status"] = "FAIL"
                if not symbolic_audit.get("issues"):
                    symbolic_audit["issues"] = list(
                        ref_errors
                        or [
                            f"Wykryto niespójność wskaźników symbolicznych \ref_ast / \ref_csv w zadaniu {current_task.get('task_id')} na węźle {target_node}."
                        ]
                    )
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

        failed_file = node_path if not overall_pass else None

        report = ValidationReport(
            status="PASS" if overall_pass else "FAIL",
            failed_task_id=None if overall_pass else current_task.get("task_id"),
            failed_node=None if overall_pass else target_node,
            failed_file=failed_file,
            failed_agent=None if overall_pass else current_task.get("assigned_agent"),
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
            report["warnings"] = contract_warnings

        write_json_state(self.validation_report_path, report)
        return report

    def _audit_factual_state(self, report: dict[str, Any]) -> dict[str, Any]:
        """Read the workspace as it is. The next queue is built from this, not from the abandoned plan."""
        test_res = run_isolated_tests(
            self.workspace_dir,
            use_docker=False,
            verification_dir=self.adk_root / "tools" / "verification",
        )
        files: list[str] = []
        if self.workspace_dir.exists():
            for path in sorted(self.workspace_dir.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and ".compiled." not in path.name:
                    files.append(path.relative_to(self.workspace_dir).as_posix())

        chapters_present: list[int] = []
        thesis = self.workspace_dir / "thesis.md"
        if thesis.exists():
            for match in re.finditer(r"^##\s+.*?(\d+)", thesis.read_text(encoding="utf-8"), flags=re.MULTILINE):
                number = int(match.group(1))
                if 1 <= number <= 6 and number not in chapters_present:
                    chapters_present.append(number)
        chapters_missing = [n for n in range(1, 7) if n not in chapters_present] if self.include_docs else []

        symbolic_errors: list[str] = []
        if thesis.exists() and self.include_docs:
            compiled = compile_symbolic_references(thesis, self.workspace_dir)
            symbolic_errors = _fit_items([str(err) for err in compiled.get("errors", [])])

        csv_columns: list[str] = []
        csv_path = self.workspace_dir / "results.csv"
        if csv_path.exists():
            header = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
            csv_columns = [part.strip() for part in header[0].split(",")] if header else []

        trigger_issues = _collect_report_issues(report)
        audit = {
            "files": files,
            "pytest_status": test_res.get("status"),
            "pytest_errors": [str(err) for err in test_res.get("errors", [])][:8],
            "chapters_present": chapters_present,
            "chapters_missing": chapters_missing,
            "symbolic_errors": symbolic_errors,
            "csv_columns": csv_columns,
            "trigger_issues": [str(item) for item in trigger_issues],
        }
        write_json_state(self.state_dir / "factual_audit.json", audit)
        return audit

    def _pdf_failure_report(self) -> dict[str, Any] | None:
        """Compile the thesis. A live failure comes back as a queue-rebuild reason. Mock stays out of this path."""
        if str(self.provider).strip().lower() == "mock":
            return None
        thesis_md = self.workspace_dir / "thesis.md"
        if not thesis_md.exists():
            return {"status": "FAIL", "issues": ["Brak thesis.md, nie ma czego kompilować do PDF."]}
        try:
            from adk.benchmarks.tasks import BenchmarkTaskSpec
            from adk.tools.building.thesis_publisher import build_latex_source, compile_latex_to_pdf

            blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
            spec = BenchmarkTaskSpec(
                task_id=str(blueprint.get("task_id") or "live"),
                slug=str(blueprint.get("slug") or "live"),
                title_pl=str(blueprint.get("title_pl") or blueprint.get("title") or "Praca dyplomowa"),
                title_en=str(blueprint.get("title_en") or blueprint.get("title_pl") or "Thesis"),
                domain=str(blueprint.get("domain") or "general"),
                prompt=self.current_user_prompt,
                thesis_type=str(getattr(self, "planned_thesis_type", None) or blueprint.get("thesis_type") or "inzynierska"),
                template_name=blueprint.get("template_name"),
            )
            tex_path = build_latex_source(
                spec,
                self.workspace_dir,
                template_name=spec.template_name,
                thesis_type=spec.thesis_type,
                provider=self.provider,
            )
            pdf_path = self.workspace_dir / "thesis.pdf"
            compiled = compile_latex_to_pdf(tex_path, pdf_path)
        except Exception as exc:
            return {"status": "FAIL", "issues": [f"Kompilacja PDF nie powiodła się: {exc}"]}
        if compiled and pdf_path.exists() and pdf_path.read_bytes()[:5] == b"%PDF-":
            return None
        log_path = self.workspace_dir / "logs" / "tectonic.log"
        log_text = (
            log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            if log_path.exists()
            else "brak logs/tectonic.log"
        )
        return {"status": "FAIL", "issues": [f"Kompilacja PDF nie powiodła się.\n{log_text}"]}
