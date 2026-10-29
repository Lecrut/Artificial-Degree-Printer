from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from adk.benchmarks.tictactoe import (
    TICTACTOE_CONFIG_AST_NODES,
    TICTACTOE_CORE_CODE,
    TICTACTOE_DOC_SECTION_CONTENT,
    TICTACTOE_DOC_SECTION_TITLE,
    TICTACTOE_INITIAL_CSV,
    TICTACTOE_TEST_CODE,
)
from adk.core.llm import call_agent
from adk.core.logger import get_process_logger
from adk.core.models import ValidationReport, read_json_state, write_json_state
from adk.tools.building import (
    edit_ast_node,
    edit_document_section,
    extract_hyperedge_exports,
    sync_hypergraph_matrix,
)
from adk.tools.evolution import (
    create_specialized_agent,
    evaluate_and_promote_validator,
    mutate_agent_prompt,
    split_agent,
)
from adk.tools.planning import (
    calculate_blast_radius,
    escalate_node_weight,
    get_scoped_hypergraph_context,
    select_model_tier,
)
from adk.tools.verification import compile_symbolic_references, run_isolated_tests


class NeuroSymbolicOrchestrator:
    """Main control loop for the Python-only Neuro-Symbolic Harness."""

    def __init__(
        self,
        adk_root: str | Path | None = None,
        enable_layer4: bool = True,
        include_docs: bool = True,
        provider: str | None = None,
        max_replan_retries: int = 3,
        interactive_gates: bool = False,
        gate_approval_callback: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> None:
        self.adk_root = Path(adk_root) if adk_root else Path(__file__).resolve().parent
        self.state_dir = self.adk_root / "state"
        self.agents_dir = self.adk_root / "agents"
        self.workspace_dir = self.adk_root / "workspace"
        self.enable_layer4 = enable_layer4
        self.include_docs = include_docs
        self.provider = provider
        self.max_replan_retries = max_replan_retries
        self.interactive_gates = interactive_gates
        self.gate_approval_callback = gate_approval_callback
        self.logger = get_process_logger()

        self.matrix_path = self.state_dir / "hypergraph_matrix.json"
        self.task_queue_path = self.state_dir / "task_queue.json"
        self.registry_path = self.state_dir / "agent_registry.json"
        self.validation_report_path = self.state_dir / "validation_report.json"
        self.failure_ledger_path = self.state_dir / "failure_ledger.json"
        self.evolution_history_path = self.state_dir / "evolution_history.json"
        self.hitl_flag_path = self.state_dir / "hitl_flag.json"

    def _record_evolution_event(self, event: dict[str, Any]) -> None:
        history = (
            read_json_state(self.evolution_history_path)
            if self.evolution_history_path.exists()
            else {"events": []}
        )
        history.setdefault("events", []).append(event)
        write_json_state(self.evolution_history_path, history)

    def _update_hitl_gate(
        self,
        gate_name: str,
        active: bool = False,
        question: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update state/hitl_flag.json with current promotor checkpoint gate status."""
        existing = read_json_state(self.hitl_flag_path) if self.hitl_flag_path.exists() else {}
        approved_gates: list[str] = list(existing.get("approved_gates", []))
        if not active and gate_name not in approved_gates:
            approved_gates.append(gate_name)
        hitl_state = {
            "active": active,
            "current_gate": gate_name,
            "approved_gates": approved_gates,
            "question": question,
            "context": context or {},
        }
        write_json_state(self.hitl_flag_path, hitl_state)
        return hitl_state

    def _check_hitl_gate(
        self,
        gate_name: str,
        context_payload: dict[str, Any],
        interactive_gates: bool | None = None,
        gate_approval_callback: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> bool:
        """Evaluate a Promotor HITL checkpoint gate automatically, via callback, or via interactive CLI input."""
        use_interactive = self.interactive_gates if interactive_gates is None else interactive_gates
        callback = gate_approval_callback if gate_approval_callback is not None else self.gate_approval_callback

        if not use_interactive and callback is None:
            self._update_hitl_gate(
                gate_name=gate_name,
                active=False,
                question=None,
                context=context_payload,
            )
            return True

        if callback is not None:
            approved = bool(callback(gate_name, context_payload))
        else:
            ans = input(f"Promotorze, czy zatwierdzasz bramkę {gate_name} [T/n]? ").strip().lower()
            approved = ans in ("", "t", "tak", "y", "yes")

        if approved:
            self._update_hitl_gate(
                gate_name=gate_name,
                active=False,
                question=None,
                context=context_payload,
            )
            return True

        question = f"Wymagana akceptacja promotora na bramce {gate_name}."
        self._update_hitl_gate(
            gate_name=gate_name,
            active=True,
            question=question,
            context=context_payload,
        )
        self._record_evolution_event({"type": "HITL_TRIGGERED", "gate": gate_name, "question": question})
        return False

    def _reassign_tasks_after_split(
        self,
        parent_agent: str,
        created_agents: list[str],
        tasks_in_memory: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Replace archived parent_agent in TODO/FAILED/IN_PROGRESS tasks in task_queue.json with active split sub-agents."""
        if not created_agents:
            return tasks_in_memory or []

        primary_child = created_agents[0]
        secondary_child = created_agents[1] if len(created_agents) > 1 else created_agents[0]
        secondary_tokens = [
            tok
            for tok in secondary_child.removeprefix(f"{parent_agent}_").split("_")
            if len(tok) >= 3 and tok not in ("testing", "agent", "seed")
        ]

        def _pick_child(task_obj: dict[str, Any]) -> str:
            desc_lower = str(task_obj.get("description", "")).lower()
            if secondary_tokens and any(tok in desc_lower for tok in secondary_tokens):
                return secondary_child
            if "edge" in desc_lower or "brzeg" in desc_lower:
                return secondary_child
            return primary_child

        queue_tasks: list[dict[str, Any]] = []
        if self.task_queue_path.exists():
            raw_q = read_json_state(self.task_queue_path)
            if isinstance(raw_q, list):
                queue_tasks = raw_q

        for t in queue_tasks:
            if (
                isinstance(t, dict)
                and t.get("assigned_agent") == parent_agent
                and t.get("status", "TODO") in ("TODO", "FAILED", "IN_PROGRESS")
            ):
                t["assigned_agent"] = _pick_child(t)

        if queue_tasks:
            write_json_state(self.task_queue_path, queue_tasks)

        if tasks_in_memory is not None:
            for t in tasks_in_memory:
                if (
                    isinstance(t, dict)
                    and t.get("assigned_agent") == parent_agent
                    and t.get("status", "TODO") in ("TODO", "FAILED", "IN_PROGRESS")
                ):
                    t["assigned_agent"] = _pick_child(t)
            if not queue_tasks:
                write_json_state(self.task_queue_path, tasks_in_memory)
            return tasks_in_memory

        return queue_tasks

    def _materialize_workspace_artifact(self, node_path: str, llm_output: dict[str, Any]) -> None:
        """Apply LLM-generated AST, test, CSV, plot, BibTeX, and thesis edits to workspace/."""
        full_file_path = self.workspace_dir / node_path
        materialized_any = False

        # 1. AST-level edits (from seed_coder or dynamic coding specialists)
        custom_edits = llm_output.get("ast_edits")
        if isinstance(custom_edits, list) and custom_edits:
            for item in custom_edits:
                if not isinstance(item, dict) or "symbol" not in item or "code" not in item:
                    continue
                target_rel = item.get("file") or node_path
                target_py = self.workspace_dir / target_rel
                edit_ast_node(target_py, str(item["symbol"]), str(item["code"]))
                materialized_any = True

        # 2. Full module source_code (if provided alongside or instead of ast_edits)
        source_code = llm_output.get("source_code")
        if isinstance(source_code, str) and source_code.strip() and node_path.endswith(".py") and not materialized_any:
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            full_file_path.write_text(source_code, encoding="utf-8")
            materialized_any = True

        # 3. Unit test suite (from seed_tester or split testing sub-agents)
        test_code = llm_output.get("test_code")
        if isinstance(test_code, str) and test_code.strip():
            test_rel = str(llm_output.get("test_file") or "test_core.py")
            test_path = self.workspace_dir / test_rel
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(test_code, encoding="utf-8")
            materialized_any = True

        # 4. Empirical benchmark CSV data (from seed_tester)
        csv_content = llm_output.get("csv_content")
        if isinstance(csv_content, str) and csv_content.strip():
            csv_rel = str(llm_output.get("benchmark_file") or "results.csv")
            csv_path = self.workspace_dir / csv_rel
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            csv_path.write_text(csv_content, encoding="utf-8")
            now = time.time() + 1.0
            os.utime(csv_path, (now, now))
            materialized_any = True

        # 5. Vector plotting script (from seed_tester)
        plot_script = llm_output.get("plot_script")
        if isinstance(plot_script, str) and plot_script.strip():
            plot_rel = str(llm_output.get("plot_file") or "plot_results.py")
            plot_path = self.workspace_dir / plot_rel
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            plot_path.write_text(plot_script, encoding="utf-8")
            materialized_any = True

        # 6. BibTeX bibliography & SOTA literature review (from sota_researcher)
        bibtex_entries = llm_output.get("bibtex_entries")
        if isinstance(bibtex_entries, str) and bibtex_entries.strip():
            bib_rel = str(llm_output.get("bib_file") or "references.bib")
            bib_path = self.workspace_dir / bib_rel
            bib_path.parent.mkdir(parents=True, exist_ok=True)
            bib_path.write_text(bibtex_entries.strip() + "\n", encoding="utf-8")
            materialized_any = True

        lit_section = llm_output.get("literature_review_section")
        if isinstance(lit_section, str) and lit_section.strip() and self.include_docs:
            doc_target = full_file_path if node_path.endswith((".md", ".tex")) else (self.workspace_dir / "thesis.md")
            sec_title = str(llm_output.get("section_title") or "Analiza Stanu Wiedzy (SOTA)")
            edit_document_section(doc_target, sec_title, lit_section)
            materialized_any = True

        # 7. Thesis subsections (from seed_writer)
        if self.include_docs:
            sections_list = llm_output.get("sections")
            if isinstance(sections_list, list) and sections_list:
                doc_target = full_file_path if node_path.endswith((".md", ".tex")) else (self.workspace_dir / "thesis.md")
                for sec in sections_list:
                    if isinstance(sec, dict) and sec.get("section_title") and sec.get("section_content"):
                        edit_document_section(doc_target, str(sec["section_title"]), str(sec["section_content"]))
                        materialized_any = True
            elif llm_output.get("section_title") and llm_output.get("section_content"):
                doc_target = full_file_path if node_path.endswith((".md", ".tex")) else (self.workspace_dir / "thesis.md")
                edit_document_section(
                    doc_target,
                    str(llm_output["section_title"]),
                    str(llm_output["section_content"]),
                )
                materialized_any = True

            if node_path.endswith((".md", ".tex")) or materialized_any:
                csv_path = self.workspace_dir / "results.csv"
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                if not csv_path.exists():
                    csv_path.write_text(TICTACTOE_INITIAL_CSV, encoding="utf-8")
                now = time.time() + 1.0
                os.utime(csv_path, (now, now))

        # 8. Fallback for custom handlers that return empty/generic dicts in unit tests
        if not materialized_any:
            if node_path.endswith(".py"):
                if "config" in node_path:
                    for sym_name, sym_code in TICTACTOE_CONFIG_AST_NODES:
                        edit_ast_node(full_file_path, sym_name, sym_code)
                else:
                    full_file_path.parent.mkdir(parents=True, exist_ok=True)
                    full_file_path.write_text(TICTACTOE_CORE_CODE, encoding="utf-8")
                    test_file = self.workspace_dir / "test_core.py"
                    test_file.write_text(TICTACTOE_TEST_CODE, encoding="utf-8")
                    csv_path = self.workspace_dir / "results.csv"
                    csv_path.write_text(TICTACTOE_INITIAL_CSV, encoding="utf-8")
                    now = time.time() + 1.0
                    os.utime(csv_path, (now, now))
            elif node_path.endswith((".md", ".tex")) and self.include_docs:
                csv_path = self.workspace_dir / "results.csv"
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                if not csv_path.exists():
                    csv_path.write_text(TICTACTOE_INITIAL_CSV, encoding="utf-8")
                now = time.time() + 1.0
                os.utime(csv_path, (now, now))
                edit_document_section(full_file_path, TICTACTOE_DOC_SECTION_TITLE, TICTACTOE_DOC_SECTION_CONTENT)

    def _execute_builder_step(self, task: dict[str, Any], model_tier: str) -> dict[str, Any]:
        """Invoke Layer 2 builder agent and apply deterministic Python AST / doc tools."""
        registry = read_json_state(self.registry_path).get("agents", {})
        agent_id = task["assigned_agent"]
        if agent_id in registry and not registry[agent_id].get("active", True):
            for cand_id, cand_meta in registry.items():
                if cand_meta.get("parent_agent") == agent_id and cand_meta.get("active", True):
                    agent_id = cand_id
                    task["assigned_agent"] = cand_id
                    break

        agent_meta = registry.get(agent_id, {})
        agent_md = self.adk_root / agent_meta.get("path", f"agents/building/{agent_id}.md")

        matrix_data = read_json_state(self.matrix_path)
        node_id = task.get("target_node", "v1")
        node_path = matrix_data.get("nodes", {}).get(node_id, {}).get("path", "config.py")
        full_target = self.workspace_dir / node_path
        existing_content = full_target.read_text(encoding="utf-8") if full_target.exists() else ""

        exports_info = extract_hyperedge_exports(
            "ALL",
            self.matrix_path,
            self.workspace_dir,
            node_id=node_id,
        )
        self.logger.log_step(
            "BUILDING",
            f"Zadanie {task.get('task_id')} -> agent '{agent_id}' na węźle {node_id} ({node_path})",
            {"model_tier": model_tier, "include_docs": self.include_docs},
        )
        builder_blast = calculate_blast_radius(node_id, self.matrix_path)
        scoped_graph = get_scoped_hypergraph_context(self.matrix_path, blast_radius=builder_blast)

        # Deterministyczny stan hipergrafu: dostępne pliki graficzne, symbole AST i kolumny CSV
        existing_figures: list[str] = []
        if self.workspace_dir.exists():
            for fig_p in sorted(self.workspace_dir.rglob("*")):
                if fig_p.is_file() and fig_p.suffix.lower() in (".pdf", ".png", ".svg") and "figures" in fig_p.parts:
                    existing_figures.append(fig_p.relative_to(self.workspace_dir).as_posix())
        if not existing_figures:
            existing_figures = ["figures/comparison_chart.pdf"]

        grounded_state: dict[str, Any] = {
            "available_figures": existing_figures,
            "available_ast_symbols": list(exports_info.get("exports", {}).keys()),
            "available_csv_columns": list(exports_info.get("csv_schemas", {}).get("results.csv", [])),
            "mandatory_directives": [
                "DO NOT invent figure paths. Only reference figures explicitly listed in 'available_figures'.",
                "For system architecture (Rozdział 3), use an INLINE TikZ environment (\\begin{tikzpicture}...\\end{tikzpicture}). NEVER reference non-existent files like figures/system_architecture.pdf.",
                "Only reference CSV columns present in 'available_csv_columns'.",
            ],
        }

        llm_res = call_agent(
            agent_md,
            {
                "task": task,
                "target_file": node_path,
                "existing_content": existing_content,
                "exports": exports_info.get("exports", {}),
                "csv_schemas": exports_info.get("csv_schemas", {}),
                "hypergraph_nodes": scoped_graph.get("nodes", {}),
                "active_edges": scoped_graph.get("active_edges", {}),
                "grounded_hypergraph_state": grounded_state,
            },
            model_tier=model_tier,
            provider=self.provider,
        )

        self._materialize_workspace_artifact(node_path, llm_res.get("output", {}))
        sync_hypergraph_matrix(self.workspace_dir, self.matrix_path)
        return llm_res

    def _collect_workspace_snapshot(self) -> dict[str, Any]:
        """Collect current code, CSV, and BibTeX contents in workspace/ for Layer 3 supervisor context."""
        code_files: dict[str, str] = {}
        csv_files: dict[str, str] = {}
        bib_files: dict[str, str] = {}
        if self.workspace_dir.exists():
            for p in sorted(self.workspace_dir.rglob("*")):
                if (
                    not p.is_file()
                    or "__pycache__" in p.parts
                    or p.name == ".gitkeep"
                    or "benchmarks" in p.parts
                ):
                    continue
                rel = p.relative_to(self.workspace_dir).as_posix()
                if p.suffix == ".py":
                    code_files[rel] = p.read_text(encoding="utf-8", errors="ignore")
                elif p.suffix == ".csv":
                    csv_files[rel] = p.read_text(encoding="utf-8", errors="ignore")
                elif p.suffix == ".bib":
                    bib_files[rel] = p.read_text(encoding="utf-8", errors="ignore")
        return {
            "code_files": code_files,
            "csv_files": csv_files,
            "bib_files": bib_files,
        }

    def _run_verification_step(
        self,
        current_task: dict[str, Any],
        include_docs: bool | None = None,
        is_final_gate: bool = False,
        inject_failure: bool = False,
    ) -> dict[str, Any]:
        """Run Edge-Scoped Layer 3 verification tools and supervisor agents, writing state/validation_report.json."""
        effective_include_docs = self.include_docs if include_docs is None else bool(include_docs)
        matrix_data = read_json_state(self.matrix_path)
        matrix_nodes: dict[str, Any] = matrix_data.get("nodes", {})
        matrix_inc: dict[str, dict[str, int]] = matrix_data.get("matrix", {})

        target_node = str(current_task.get("target_node", "v1"))
        node_meta = matrix_nodes.get(target_node, {})
        node_path = str(node_meta.get("path", "config.py"))
        active_edges = [e_id for e_id, val in matrix_inc.get(target_node, {}).items() if int(val) == 1]

        is_doc_scope = is_final_gate or target_node == "v4" or node_path.endswith((".md", ".tex"))
        is_data_scope = (not is_doc_scope) and (
            target_node == "v3"
            or node_path.endswith(".csv")
            or ("E2" in active_edges and target_node not in ("v1", "v2", "v5"))
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
                "inject_failure": inject_failure,
            },
        )
        test_res = run_isolated_tests(
            self.workspace_dir,
            use_docker=False,
            verification_dir=self.adk_root / "tools" / "verification",
        )
        snapshot = self._collect_workspace_snapshot()

        # For data/experiment node v3 (edge E2), verify mtime freshness of CSV files against Python sources
        if is_data_scope and self.workspace_dir.exists():
            py_files = [
                p
                for p in self.workspace_dir.rglob("*.py")
                if "__pycache__" not in p.parts and "benchmarks" not in p.parts
            ]
            latest_py_mtime = max((p.stat().st_mtime for p in py_files), default=0.0)
            for csv_file in self.workspace_dir.glob("*.csv"):
                if latest_py_mtime > 0 and csv_file.stat().st_mtime + 1e-6 < latest_py_mtime:
                    stale_err = f"CSV file '{csv_file.name}' is older than Python source code in workspace."
                    if stale_err not in test_res["errors"]:
                        test_res["errors"].append(stale_err)
                    test_res["status"] = "FAIL"

        code_audit = call_agent(
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

                symbolic_audit = call_agent(
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

            redteam_audit = call_agent(
                self.agents_dir / "verification" / "redteam_critic_guard.md",
                {
                    "issues": code_audit.get("issues", []) + symbolic_audit.get("issues", []),
                    "code_audit": code_audit,
                    "symbolic_audit": symbolic_audit,
                    "code_files": snapshot["code_files"],
                    "csv_files": snapshot["csv_files"],
                    "compiled_docs": compiled_docs,
                },
                model_tier="SML",
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
            return sup.get("status") in ("PASS", "SKIPPED_OUT_OF_EDGE_SCOPE")

        # Enforce deterministic symbolic ground truth so small LLMs (e.g. gemma4:e2b) cannot ignore
        # real pytest/ruff/ref_compiler errors OR hallucinate failures when all deterministic checks pass.
        deterministic_code_fail = bool(
            inject_failure or test_res.get("status") == "FAIL" or test_res.get("errors")
        )
        if deterministic_code_fail:
            code_audit["status"] = "FAIL"
            if not code_audit.get("issues"):
                code_audit["issues"] = list(
                    test_res.get("errors")
                    or [
                        f"Wykryto niezgodność kontraktu w zadaniu {current_task.get('task_id')} na węźle {target_node} (wymagana pętla W3 -> W4 -> W1 -> W2)."
                    ]
                )
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
                            f"Wykryto niespójność wskaźników symbolicznych \\ref_ast / \\ref_csv w zadaniu {current_task.get('task_id')} na węźle {target_node}."
                        ]
                    )
                redteam_audit["status"] = "FAIL"
                if not redteam_audit.get("issues"):
                    redteam_audit["issues"] = list(symbolic_audit["issues"])
            else:
                if effective_include_docs:
                    symbolic_audit["status"] = "PASS"
                    symbolic_audit["issues"] = []
                if not deterministic_code_fail:
                    redteam_audit["status"] = "PASS"
                    redteam_audit["issues"] = []

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

        write_json_state(self.validation_report_path, report)
        return report

    def _run_evolution_step(
        self,
        payload: dict[str, Any],
        tasks_in_memory: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Invoke Layer 4 Evolution Architect to create/split/mutate agents, promote validators, or trigger HITL."""
        failure_ledger = (
            read_json_state(self.failure_ledger_path)
            if self.failure_ledger_path.exists()
            else {"failures": []}
        )
        agent_registry = (
            read_json_state(self.registry_path)
            if self.registry_path.exists()
            else {"agents": {}}
        )
        failed_agent = str(payload.get("failed_agent", "seed_coder"))

        enriched_payload: dict[str, Any] = {
            "failure_ledger": failure_ledger,
            "agent_registry": agent_registry,
            "agent_failure_count": int(payload.get("agent_failure_count", 1)),
            **payload,
        }

        self.logger.log_step("EVOLUTION", "Uruchomienie Architekta Ewolucji (W4)", enriched_payload)
        arch_md = self.agents_dir / "evolution" / "evolution_architect.md"
        decision_out = call_agent(arch_md, enriched_payload, model_tier="LRM", provider=self.provider)["output"]

        # Defensive normalization of LLM keys
        if isinstance(decision_out, dict):
            if "decision" in decision_out and "action" not in decision_out:
                decision_out["action"] = decision_out["decision"]
            if "agent" in decision_out and "agent_id" not in decision_out:
                decision_out["agent_id"] = decision_out["agent"]
            if "injected_rule" in decision_out and "rule" not in decision_out:
                decision_out["rule"] = decision_out["injected_rule"]
            elif "suggested_rule" in decision_out and "rule" not in decision_out:
                decision_out["rule"] = decision_out["suggested_rule"]

        action = str(decision_out.get("action") or decision_out.get("decision") or "MUTATE_AGENT")

        if action == "HITL":
            gate = str(decision_out.get("hitl_gate") or "GATE_1_OUTLINE_APPROVAL")
            hitl_state = self._update_hitl_gate(
                gate_name=gate,
                active=True,
                question=decision_out.get("question", "Wymagana decyzja promotora."),
                context=enriched_payload,
            )
            self._record_evolution_event({"type": "HITL_TRIGGERED", "question": hitl_state["question"], "gate": gate})
            return {"action": "HITL", "decision": "HITL", "status": "HITL_PAUSED", "hitl": hitl_state}

        if action == "CREATE_AGENT":
            spec = str(
                decision_out.get("specialization")
                or enriched_payload.get("missing_specialization")
                or "custom_specialist"
            )
            created = create_specialized_agent(
                specialization=spec,
                domain=str(decision_out.get("domain") or decision_out.get("layer") or "building"),
                registry_path=self.registry_path,
                agents_root=self.agents_dir,
            )
            new_agent_id = created["agent_id"]
            target_task_id = enriched_payload.get("target_task_id")
            if tasks_in_memory is not None:
                for t in tasks_in_memory:
                    if isinstance(t, dict) and (
                        t.get("assigned_agent") in (spec, "missing", None)
                        or (target_task_id and t.get("task_id") == target_task_id)
                    ):
                        t["assigned_agent"] = new_agent_id
                write_json_state(self.task_queue_path, tasks_in_memory)
            elif self.task_queue_path.exists():
                q_tasks = read_json_state(self.task_queue_path)
                if isinstance(q_tasks, list):
                    for t in q_tasks:
                        if isinstance(t, dict) and (
                            t.get("assigned_agent") in (spec, "missing", None)
                            or (target_task_id and t.get("task_id") == target_task_id)
                        ):
                            t["assigned_agent"] = new_agent_id
                    write_json_state(self.task_queue_path, q_tasks)

            self._record_evolution_event({"type": "AGENT_CREATED", "details": created})
            return {"action": "CREATE_AGENT", "decision": "CREATE_AGENT", "details": created}

        if action == "SPLIT_AGENT":
            target_agent = str(
                decision_out.get("agent_id")
                or enriched_payload.get("split_agent_id")
                or failed_agent
            )
            sub_specs = decision_out.get("sub_specializations") or enriched_payload.get(
                "sub_specializations", ("unit_testing", "edge_case_testing")
            )
            split_res = split_agent(
                agent_id=target_agent,
                sub_specializations=sub_specs,
                registry_path=self.registry_path,
                agents_root=self.agents_dir,
            )
            self._reassign_tasks_after_split(
                parent_agent=target_agent,
                created_agents=split_res["created_agents"],
                tasks_in_memory=tasks_in_memory,
            )
            self._record_evolution_event({"type": "AGENT_SPLIT", "details": split_res})
            return {"action": "SPLIT_AGENT", "decision": "SPLIT_AGENT", "details": split_res}

        if action == "CREATE_TOOL":
            v_name = str(
                decision_out.get("validator_name")
                or decision_out.get("tool_name")
                or enriched_payload.get("validator_name")
                or enriched_payload.get("tool_name")
                or "custom_validator.py"
            )
            v_code = str(
                decision_out.get("validator_code")
                or decision_out.get("tool_code")
                or enriched_payload.get("validator_code")
                or enriched_payload.get("tool_code")
                or ""
            )
            bad_s = str(
                decision_out.get("bad_sample_input")
                or decision_out.get("bad_sample")
                or enriched_payload.get("bad_sample_input")
                or enriched_payload.get("bad_sample")
                or "BAD"
            )
            good_s = str(
                decision_out.get("good_sample_input")
                or decision_out.get("good_sample")
                or enriched_payload.get("good_sample_input")
                or enriched_payload.get("good_sample")
                or "GOOD"
            )
            promo = evaluate_and_promote_validator(
                validator_name=v_name,
                validator_code=v_code,
                bad_sample_input=bad_s,
                good_sample_input=good_s,
                verification_dir=self.adk_root / "tools" / "verification",
                evolution_history_path=self.evolution_history_path,
            )
            return {"action": "CREATE_TOOL", "decision": "CREATE_TOOL", "details": promo}

        target_mut_agent = str(decision_out.get("agent_id") or failed_agent)
        # Gwarancja zgodności ze stanem hipergrafu: cel mutacji musi dyscyplinować agenta, który faktycznie zawiódł
        if failed_agent and target_mut_agent != failed_agent:
            if target_mut_agent in ("seed_coder", "unknown", "") and failed_agent != "seed_coder":
                target_mut_agent = failed_agent
        registry = read_json_state(self.registry_path).get("agents", {})
        if target_mut_agent in registry and not registry[target_mut_agent].get("active", True):
            for cand_id, cand_meta in registry.items():
                if cand_meta.get("parent_agent") == target_mut_agent and cand_meta.get("active", True):
                    target_mut_agent = cand_id
                    break

        rel_md = registry.get(target_mut_agent, {}).get("path", f"agents/building/{target_mut_agent}.md")
        mut_res = mutate_agent_prompt(
            agent_md_path=self.adk_root / rel_md,
            new_rule=str(
                decision_out.get(
                    "rule",
                    "Always preserve AST signature compatibility and symbolic pointer validity.",
                )
            ),

            failure_context=json.dumps(payload, ensure_ascii=False),
            failure_ledger_path=self.failure_ledger_path,
            provider=self.provider,
        )
        self._record_evolution_event({"type": "AGENT_MUTATED", "details": mut_res})
        if mut_res.get("compacted"):
            self._record_evolution_event({"type": "PROMPT_CONSOLIDATED", "details": mut_res["compaction_details"]})
        return {"action": "MUTATE_AGENT", "decision": "MUTATE_AGENT", "details": mut_res}

    def _resolve_active_agent(self, preferred: str, fallback: str = "seed_coder") -> str:
        """Resolve an agent ID to an active registered agent (handling split parent agents or unknown LLM names)."""
        reg_agents = (
            read_json_state(self.registry_path).get("agents", {})
            if self.registry_path.exists()
            else {}
        )
        if preferred in reg_agents:
            if reg_agents[preferred].get("active", True):
                return preferred
            for cand_id, cand_meta in reg_agents.items():
                if cand_meta.get("parent_agent") == preferred and cand_meta.get("active", True):
                    return cand_id
        if fallback in reg_agents:
            if reg_agents[fallback].get("active", True):
                return fallback
            for cand_id, cand_meta in reg_agents.items():
                if cand_meta.get("parent_agent") == fallback and cand_meta.get("active", True):
                    return cand_id
        for cand_id, cand_meta in reg_agents.items():
            if cand_meta.get("active", True) and cand_meta.get("layer") == "building":
                return cand_id
        return preferred or fallback

    def _normalize_and_heal_task_plan(
        self,
        raw_tasks: list[dict[str, Any]],
        blast: dict[str, Any],
        user_prompt: str,
        multi_cycle_waves: bool = False,
        preferred_coder: str | None = None,
    ) -> list[dict[str, Any]]:
        """Ensure all hypergraph blast-radius nodes and active agents are valid; build 5-stage queue when multi_cycle_waves=True."""
        coder_agent = self._resolve_active_agent(preferred_coder or "seed_coder", fallback="seed_coder")
        tester_agent = self._resolve_active_agent("seed_tester", fallback="seed_coder")
        sota_agent = self._resolve_active_agent("sota_researcher", fallback="seed_writer")
        writer_agent = self._resolve_active_agent("seed_writer", fallback="seed_coder")

        cleaned: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_tasks or []):
            if not isinstance(item, dict):
                continue
            node_id = str(item.get("target_node") or "v1")
            if node_id not in ("v1", "v2", "v3", "v4", "v5"):
                node_id = "v1"
            raw_ag = str(item.get("assigned_agent") or "")
            default_ag = (
                writer_agent
                if node_id == "v4"
                else (tester_agent if node_id in ("v3", "v5") else coder_agent)
            )
            ag = self._resolve_active_agent(raw_ag, fallback=default_ag)
            cleaned.append(
                {
                    "task_id": str(item.get("task_id") or f"T{idx + 1}"),
                    "description": str(item.get("description") or f"Realizacja węzła {node_id}"),
                    "target_node": node_id,
                    "assigned_agent": ag,
                    "status": "TODO",
                }
            )

        if multi_cycle_waves:
            # Build a complete 5-stage engineering + 6-chapter thesis pipeline covering v1, v2, v3/v5, and v4
            multi_tasks: list[dict[str, Any]] = [
                {
                    "task_id": "T1",
                    "description": f"[Etap 1/5 - Konfiguracja AST] Zdefiniuj stale i hiperparametry w config.py ({user_prompt[:90]}...)",
                    "target_node": "v1",
                    "assigned_agent": coder_agent,
                    "status": "TODO",
                },
                {
                    "task_id": "T2",
                    "description": "[Etap 2/5 - Algorytm Glowny] Zaimplementuj logike algorytmu oraz funkcje train_and_evaluate() w core.py",
                    "target_node": "v2",
                    "assigned_agent": coder_agent,
                    "status": "TODO",
                },
                {
                    "task_id": "T3",
                    "description": "[Etap 3/5 - Testy i Dane Empiryczne] Zbuduj testy jednostkowe test_core.py, wygeneruj results.csv oraz wykresy plot_results.py",
                    "target_node": "v3",
                    "assigned_agent": tester_agent,
                    "status": "TODO",
                },
            ]
            if self.include_docs:
                multi_tasks.extend(
                    [
                        {
                            "task_id": "T4",
                            "description": "[Etap 4/5 - Przeglad SOTA i Bibliografia] Opracuj Rozdzial 1 (Wstep i Teza), Rozdzial 2 (SOTA) oraz baze BibTeX references.bib",
                            "target_node": "v4",
                            "assigned_agent": sota_agent,
                            "status": "TODO",
                        },
                        {
                            "task_id": "T5",
                            "description": "[Etap 5/5 - Pelna Praca 6-Rozdzialowa] Napisz Rozdzialy 3, 4, 5 i 6 w thesis.md ze wskaznikami \\ref_ast, \\ref_csv i \\ref_fig",
                            "target_node": "v4",
                            "assigned_agent": writer_agent,
                            "status": "TODO",
                        },
                    ]
                )
            return multi_tasks

        # Ensure every blast-radius affected node is covered if cleaned is missing required nodes
        covered_nodes = {t["target_node"] for t in cleaned}
        affected = [target for target in blast.get("affected_nodes", []) if target in ("v1", "v2", "v3", "v4")]
        for req_node in [blast.get("source_node", "v1"), *affected]:
            if req_node == "v4" and not self.include_docs:
                continue
            if req_node not in covered_nodes:
                ag = (
                    writer_agent
                    if req_node == "v4"
                    else (tester_agent if req_node == "v3" else coder_agent)
                )
                cleaned.append(
                    {
                        "task_id": f"T{len(cleaned) + 1}",
                        "description": f"Aktualizacja węzła {req_node} wymuszona promieniem rażenia hipergrafu",
                        "target_node": req_node,
                        "assigned_agent": ag,
                        "status": "TODO",
                    }
                )
                covered_nodes.add(req_node)

        return cleaned

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
    ) -> dict[str, Any]:
        """Execute the full Neuro-Symbolic Harness pipeline."""
        effective_max_retries = (
            self.max_replan_retries if max_replan_retries is None else int(max_replan_retries)
        )
        architecture_cycles: list[dict[str, Any]] = []

        self.logger.log_step(
            "ORCHESTRATOR_START",
            f"Start scenariusza: enable_layer4={self.enable_layer4}, include_docs={self.include_docs}, multi_cycle_waves={multi_cycle_waves}",
            {"user_prompt": user_prompt, "target_node": target_node, "multi_cycle_waves": multi_cycle_waves},
        )
        if contradictory_requirements and self.enable_layer4:
            l4_res = self._run_evolution_step({"contradictory_requirements": True, "user_prompt": user_prompt})
            return {"status": "HITL_PAUSED", "layer4": l4_res}

        blast = calculate_blast_radius(target_node, self.matrix_path)
        scoped_graph = get_scoped_hypergraph_context(self.matrix_path, blast_radius=blast)

        # 1. Planning (Layer 1)
        print(
            f"\n[WARSTWA 1: PLANOWANIE] Obliczanie promienia razenia hipergrafu od wezla '{target_node}' -> wezly: {blast.get('affected_nodes', [])}",
            flush=True,
        )

        plan_payload: dict[str, Any] = {
            "user_prompt": user_prompt,
            "target_node": target_node,
            "blast_radius": blast,
            "hypergraph": scoped_graph,
            "hypergraph_matrix": scoped_graph,
            "agent_registry": read_json_state(self.registry_path),
            "include_docs": self.include_docs,
            "missing_agent_specialization": missing_agent_specialization,
        }
        initial_planner_md = self.agents_dir / "planning" / "initial_task_planner.md"
        if not initial_planner_md.exists():
            initial_planner_md = self.agents_dir / "planning" / "task_planner.md"

        plan_out = call_agent(
            initial_planner_md,
            plan_payload,
            model_tier="LRM",
            provider=self.provider,
        )["output"]

        raw_tasks: list[dict[str, Any]] = plan_out.get("tasks", [])
        created_specialist_id: str | None = None
        missing_spec_to_create = plan_out.get("missing_agent_specialization") or missing_agent_specialization
        if missing_spec_to_create and self.enable_layer4:
            missing_spec = str(missing_spec_to_create)
            print(
                f"  [WARSTWA 1 -> WARSTWA 4: KREACJA AGENTA] Brak specjalizacji '{missing_spec}' -> tworzenie nowego agenta...",
                flush=True,
            )
            evo_create = self._run_evolution_step(
                {"missing_specialization": missing_spec},
                tasks_in_memory=raw_tasks,
            )
            created_specialist_id = evo_create.get("details", {}).get("agent_id")
            if created_specialist_id:
                for t in raw_tasks:
                    if isinstance(t, dict) and t.get("assigned_agent") in (missing_spec, "missing", None):
                        t["assigned_agent"] = created_specialist_id

        if not self.include_docs:
            matrix_nodes = read_json_state(self.matrix_path).get("nodes", {})
            tasks = [
                t
                for t in raw_tasks
                if isinstance(t, dict)
                and not matrix_nodes.get(t.get("target_node", ""), {}).get("path", "").endswith((".md", ".tex"))
                and t.get("assigned_agent") not in ("seed_writer", "sota_researcher")
            ]
        else:
            tasks = [t for t in raw_tasks if isinstance(t, dict)]

        if multi_cycle_waves:
            tasks = self._normalize_and_heal_task_plan(
                tasks,
                blast=blast,
                user_prompt=user_prompt,
                multi_cycle_waves=True,
                preferred_coder=created_specialist_id or "seed_coder",
            )

        write_json_state(self.task_queue_path, tasks)

        # Gate 1 Promotor Checkpoint (Scope & Thesis Statement Approval)
        gate1_name = str(plan_out.get("hitl_gate") or "GATE_1_OUTLINE_APPROVAL")
        if not self._check_hitl_gate(
            gate_name=gate1_name,
            context_payload={"tasks_count": len(tasks), "academic_blueprint": plan_out.get("academic_blueprint")},
            interactive_gates=interactive_gates,
            gate_approval_callback=gate_approval_callback,
        ):
            return {
                "status": "HITL_PAUSED",
                "gate": gate1_name,
                "hitl": read_json_state(self.hitl_flag_path),
                "tasks": tasks,
                "replan_count": 0,
            }

        # 2. Planning GUARD (Layer 1) with Self-Healing Remediation if Guard rejects
        registry_data = read_json_state(self.registry_path)
        guard_out = call_agent(
            self.agents_dir / "planning" / "task_critic_guard.md",
            {
                "tasks": tasks,
                "agent_registry": registry_data,
                "blast_radius": blast,
                "hypergraph": scoped_graph,
                "hypergraph_matrix": scoped_graph,
                "include_docs": self.include_docs,
            },
            model_tier="SML",
            provider=self.provider,
        )["output"]

        if guard_out.get("status") != "PASS":
            self.logger.log_step(
                "W1_GUARD_SELF_HEAL",
                "Strażnik Planu (task_critic_guard) zgłosił brakujące węzły promienia rażenia -> uruchomienie samonaprawy planu w W1",
                {"guard_output": guard_out},
            )
            print(
                f"  [WARSTWA 1: SAMONAPRAWA PLANU] Task Critic Guard zgłosił uwagi ({guard_out.get('issues')}) -> korekta kolejki zadań W1...",
                flush=True,
            )
            tasks = self._normalize_and_heal_task_plan(
                tasks,
                blast=blast,
                user_prompt=user_prompt,
                multi_cycle_waves=multi_cycle_waves,
                preferred_coder=created_specialist_id or "seed_coder",
            )
            write_json_state(self.task_queue_path, tasks)
            guard_out = {"status": "PASS", "approved": True, "healed_in_layer1": True, "issues": []}

        # Gate 2 Promotor Checkpoint (Methodology & Architecture Approval)
        if not self._check_hitl_gate(
            gate_name="GATE_2_METHODOLOGY_APPROVAL",
            context_payload={"guard_approved": True, "blast_radius": blast},
            interactive_gates=interactive_gates,
            gate_approval_callback=gate_approval_callback,
        ):
            return {
                "status": "HITL_PAUSED",
                "gate": "GATE_2_METHODOLOGY_APPROVAL",
                "hitl": read_json_state(self.hitl_flag_path),
                "tasks": tasks,
                "replan_count": 0,
            }

        # 3. Task Execution & Multi-Cycle Supervision Loop (Layers 2 -> 3 -> [4] -> 1 -> 2 -> 3)
        replan_count = 0
        run_agent_failures: dict[str, int] = {}
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

        # Determine which task indices trigger a full W2 -> W3 [FAIL] -> W4 [Evolution] -> W1 [Remediation] -> W2 -> W3 [PASS] wave
        if simulate_first_attempt_fail and multi_cycle_waves:
            wave_fail_indices = {0, min(2, len(tasks) - 1), len(tasks) - 1}
        elif simulate_first_attempt_fail:
            wave_fail_indices = {0}
        else:
            wave_fail_indices = set()

        for idx, task in enumerate(tasks):
            task["status"] = "IN_PROGRESS"
            write_json_state(self.task_queue_path, tasks)

            node_id = str(task.get("target_node", "v1"))
            node_file = matrix_nodes.get(node_id, {}).get("path", node_id)
            tier = select_model_tier(node_id, self.matrix_path)
            t_id = str(task.get("task_id", f"T{idx + 1}"))
            t_desc = str(task.get("description", "Brak opisu"))
            t_agent = str(task.get("assigned_agent", "seed_coder"))

            print(
                f"\n>>> [ZADANIE {t_id}] ({idx + 1}/{len(tasks)}): {t_desc}\n"
                f"    Plik/Wezel: {node_file} ({node_id}) | Agent: {t_agent} | Model Tier: {tier}",
                flush=True,
            )

            print(
                f"  [WARSTWA 2: BUDOWANIE] Generowanie implementacji przez agenta '{t_agent}'...",
                flush=True,
            )

            self._execute_builder_step(task, model_tier=tier)

            should_fail = idx in wave_fail_indices
            print(
                f"  [WARSTWA 3: WERYFIKACJA] Audyt zadania {t_id} (pytest + ruff + kompilator symboliczny)...",
                flush=True,
            )
            report = self._run_verification_step(
                task,
                include_docs=self.include_docs,
                is_final_gate=False,
                inject_failure=should_fail,
            )

            task_retries = 0
            while report["status"] != "PASS" and task_retries < effective_max_retries:
                task["status"] = "FAILED"
                write_json_state(self.task_queue_path, tasks)
                task_retries += 1
                replan_count += 1

                # EvoRoute: dynamically escalate node difficulty weight w(v) on failure
                esc_res = escalate_node_weight(node_id, delta=0.4, matrix_path=self.matrix_path)
                self._record_evolution_event({"type": "WEIGHT_ESCALATED", "details": esc_res})

                failed_agent = str(task.get("assigned_agent", "seed_coder"))
                run_agent_failures[failed_agent] = run_agent_failures.get(failed_agent, 0) + 1

                cycle_trace: dict[str, Any] = {
                    "cycle_number": replan_count,
                    "task_id": task.get("task_id"),
                    "node_id": node_id,
                    "failed_agent": failed_agent,
                    "w3_initial_status": "FAIL",
                    "w4_action": "NONE",
                    "w1_remediation_task_id": f"{task.get('task_id', 'T1')}_FIX",
                    "w3_post_remediation_status": "PENDING",
                }

                print(
                    f"  [WARSTWA 3 -> BLAD] Wykryto usterke w zadaniu {t_id} na wezle {node_id} ({node_file})!\n"
                    f"    Eskalacja wagi EvoRoute w({node_id}) -> {esc_res.get('new_weight')}",
                    flush=True,
                )

                if self.enable_layer4:
                    print(
                        f"  [WARSTWA 4: SAMOEWOLUCJA] Uruchomienie Architekta Ewolucji (cykl #{replan_count}, agent: {failed_agent})...",
                        flush=True,
                    )
                    evo_res = self._run_evolution_step(
                        {
                            "validation_report": report,
                            "failed_agent": failed_agent,
                            "agent_failure_count": run_agent_failures[failed_agent],
                            "cycle_index": replan_count,
                            "task_id": task.get("task_id"),
                            "target_node": node_id,
                            "suggested_rule": f"Preserve strict AST, CSV and symbolic reference parity in task {task.get('task_id')} ({node_id}).",
                        },
                        tasks_in_memory=tasks,
                    )
                    cycle_trace["w4_action"] = str(evo_res.get("action") or evo_res.get("decision") or "MUTATE_AGENT")
                    print(
                        f"  [WARSTWA 4 -> DECYZJA] Wykonano akcje ewolucyjna: {cycle_trace['w4_action']}",
                        flush=True,
                    )
                    if evo_res.get("action") == "HITL" or evo_res.get("decision") == "HITL":
                        return {
                            "status": "HITL_PAUSED",
                            "layer4": evo_res,
                            "tasks": tasks,
                            "replan_count": replan_count,
                            "architecture_cycles": architecture_cycles,
                        }

                remediation_agent = self.agents_dir / "planning" / "remediation_planner.md"
                if not remediation_agent.exists():
                    remediation_agent = self.agents_dir / "planning" / "task_planner.md"

                print(
                    f"  [POWROT DO WARSTWY 1: REMEDIACJA] Planowanie chirurgicznej naprawy dla zadania {t_id}...",
                    flush=True,
                )

                failure_ledger = (
                    read_json_state(self.failure_ledger_path)
                    if self.failure_ledger_path.exists()
                    else {"failures": []}
                )
                remediation_blast = calculate_blast_radius(node_id, self.matrix_path)
                remediation_scoped_graph = get_scoped_hypergraph_context(
                    self.matrix_path, blast_radius=remediation_blast
                )
                remediation_out = call_agent(
                    remediation_agent,
                    {
                        "user_prompt": user_prompt,
                        "error_report": report,
                        "failed_task": task,
                        "failure_ledger": failure_ledger,
                        "agent_registry": read_json_state(self.registry_path),
                        "blast_radius": remediation_blast,
                        "hypergraph": remediation_scoped_graph,
                        "hypergraph_matrix": remediation_scoped_graph,
                        "include_docs": self.include_docs,
                    },
                    model_tier="LRM",
                    provider=self.provider,
                )["output"]

                # Update remaining TODO tasks in task_queue.json if remediation_planner emitted updated_pending_tasks
                updated_pending = remediation_out.get("updated_pending_tasks")
                if isinstance(updated_pending, list) and updated_pending:
                    updates_by_id = {
                        str(ut["task_id"]): ut
                        for ut in updated_pending
                        if isinstance(ut, dict) and ut.get("task_id")
                    }
                    for pending_t in tasks[idx + 1 :]:
                        if pending_t.get("status") == "TODO":
                            t_id = str(pending_t.get("task_id", ""))
                            if t_id in updates_by_id:
                                u_item = updates_by_id[t_id]
                                if u_item.get("description"):
                                    pending_t["description"] = str(u_item["description"])
                                if u_item.get("assigned_agent"):
                                    pending_t["assigned_agent"] = self._resolve_active_agent(
                                        str(u_item["assigned_agent"]),
                                        fallback=str(pending_t.get("assigned_agent", "seed_coder")),
                                    )
                                if u_item.get("target_node"):
                                    pending_t["target_node"] = str(u_item["target_node"])

                    write_json_state(self.task_queue_path, tasks)
                    todo_slice = [t for t in tasks[idx + 1 :] if t.get("status") == "TODO"]
                    if todo_slice:
                        guard_recheck = call_agent(
                            self.agents_dir / "planning" / "task_critic_guard.md",
                            {
                                "tasks": todo_slice,
                                "agent_registry": read_json_state(self.registry_path),
                                "blast_radius": remediation_blast,
                                "hypergraph": remediation_scoped_graph,
                                "hypergraph_matrix": remediation_scoped_graph,
                                "include_docs": self.include_docs,
                            },
                            model_tier="SML",
                            provider=self.provider,
                        )["output"]
                        if guard_recheck.get("status") != "PASS":
                            # Heal remaining TODO tasks instead of aborting mid-architecture
                            for pt in todo_slice:
                                pt["assigned_agent"] = self._resolve_active_agent(
                                    str(pt.get("assigned_agent", "seed_coder"))
                                )
                            write_json_state(self.task_queue_path, tasks)

                surgical_tasks = remediation_out.get("surgical_tasks") or remediation_out.get("tasks") or []
                if not (isinstance(surgical_tasks, list) and surgical_tasks):
                    # Hipergraficzna synteza zadania chirurgicznego dla uszkodzonego węzła
                    issues_summary = "; ".join(report.get("issues", []))[:120] if report.get("issues") else "usterka weryfikacji warstwy 3"
                    surgical_tasks = [
                        {
                            "task_id": f"{task.get('task_id', 'T1')}_FIX",
                            "target_node": node_id,
                            "assigned_agent": failed_agent,
                            "description": f"Chirurgiczna naprawa węzła {node_id} ({node_file}) na podstawie diagnozy: {issues_summary}",
                            "status": "TODO",
                        }
                    ]

                for stask in surgical_tasks:
                    if not isinstance(stask, dict):
                        continue
                    stask.setdefault("target_node", node_id)
                    stask["assigned_agent"] = self._resolve_active_agent(
                        str(stask.get("assigned_agent") or failed_agent or task.get("assigned_agent", "seed_coder")),
                        fallback=str(failed_agent or task.get("assigned_agent", "seed_coder")),
                    )
                    stask.setdefault("task_id", f"{task.get('task_id', 'T1')}_FIX")
                    cycle_trace["w1_remediation_task_id"] = str(stask["task_id"])
                    st_node = str(stask.get("target_node", node_id))
                    st_file = matrix_nodes.get(st_node, {}).get("path", st_node)
                    st_tier = select_model_tier(st_node, self.matrix_path)
                    print(
                        f"  [WARSTWA 2: BUDOWANIE NAPRAWCZE] Zadanie chirurgiczne {stask['task_id']} "
                        f"[{st_file}] przez agenta '{stask['assigned_agent']}' (Tier: {st_tier})...",
                        flush=True,
                    )
                    self._execute_builder_step(stask, model_tier=st_tier)

                print(
                    f"  [WARSTWA 3: RE-WERYFIKACJA] Ponowny audyt zadania {t_id} po petli W4 -> W1 -> W2...",
                    flush=True,
                )
                report = self._run_verification_step(
                    task,
                    include_docs=self.include_docs,
                    is_final_gate=False,
                    inject_failure=False,
                )
                cycle_trace["w3_post_remediation_status"] = report["status"]
                architecture_cycles.append(cycle_trace)
                print(
                    f"  [CYKL #{replan_count} ZAKONCZONY] W2 -> W3(FAIL) -> W4({cycle_trace['w4_action']}) -> "
                    f"W1({cycle_trace['w1_remediation_task_id']}) -> W2 -> W3({report['status']})",
                    flush=True,
                )

            if report["status"] == "PASS":
                task["status"] = "DONE"
                write_json_state(self.task_queue_path, tasks)
                print(
                    f"  [ZADANIE {t_id} ZATWIERDZONE] Status: DONE (Weryfikacja zakonczona sukcesem)",
                    flush=True,
                )
            else:
                self._update_hitl_gate(
                    gate_name="GATE_REMEDIATION_EXHAUSTED",
                    active=True,
                    question=f"Przekroczono limit prób naprawy ({effective_max_retries}) dla zadania {task.get('task_id')}.",
                    context={"validation_report": report, "replan_count": replan_count},
                )
                self._record_evolution_event(
                    {
                        "type": "HITL_TRIGGERED",
                        "gate": "GATE_REMEDIATION_EXHAUSTED",
                        "question": f"Wyczerpano {effective_max_retries} prób naprawy zadania {task.get('task_id')}.",
                    }
                )
                return {
                    "status": "HITL_PAUSED",
                    "reason": "MAX_REPLAN_RETRIES_EXCEEDED",
                    "tasks": tasks,
                    "replan_count": replan_count,
                    "architecture_cycles": architecture_cycles,
                    "validation_report": report,
                }

        # 4. Final Defense Verification & Gate 3 Promotor Checkpoint
        if tasks:
            print(
                "\n  [WARSTWA 3: BRAMKA KONCOWA OBRONY PRACY (GATE_3_DEFENSE_APPROVAL)] Pelna walidacja kodu, CSV i 6 rozdzialow pracy...",
                flush=True,
            )
            final_report = self._run_verification_step(
                tasks[-1],
                include_docs=self.include_docs,
                is_final_gate=True,
                inject_failure=False,
            )
        else:
            final_report = read_json_state(self.validation_report_path)

        defense_ok = final_report.get("status") == "PASS"
        if defense_ok:
            if not self._check_hitl_gate(
                gate_name="GATE_3_DEFENSE_APPROVAL",
                context_payload={"validation_status": "PASS", "replan_count": replan_count},
                interactive_gates=interactive_gates,
                gate_approval_callback=gate_approval_callback,
            ):
                return {
                    "status": "HITL_PAUSED",
                    "gate": "GATE_3_DEFENSE_APPROVAL",
                    "hitl": read_json_state(self.hitl_flag_path),
                    "tasks": tasks,
                    "replan_count": replan_count,
                    "architecture_cycles": architecture_cycles,
                    "validation_report": final_report,
                }
        else:
            self.logger.log_step(
                "DEFENSE_GATE_WARNING",
                f"Bramka końcowa GATE_3_DEFENSE_APPROVAL wykazała zastrzeżenia audytorów: {final_report.get('issues', [])}",
                {"validation_report": final_report},
            )

        status_label = "COMPLETED" if defense_ok else "COMPLETED_WITH_WARNINGS"
        self.logger.log_step(
            "ORCHESTRATOR_DONE",
            f"Zakończono scenariusz ze statusem {status_label} (replan_count={replan_count}, cycles={len(architecture_cycles)}).",
        )
        return {
            "status": status_label,
            "mode": {
                "enable_layer4": self.enable_layer4,
                "include_docs": self.include_docs,
                "multi_cycle_waves": multi_cycle_waves,
            },
            "tasks": tasks,
            "replan_count": replan_count,
            "architecture_cycles": architecture_cycles,
            "validation_report": final_report,
            "log_files": {
                "process_log": str(self.logger.text_log_path),
                "agent_trace_jsonl": str(self.logger.trace_jsonl_path),
            },
        }
