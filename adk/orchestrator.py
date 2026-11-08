from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

from adk.core.connection import LLMConnectionManager
from adk.core.llm import call_agent
from adk.core.logger import get_process_logger
from adk.core.models import ValidationReport, read_json_state, write_json_state
from adk.tools.building import (
    edit_ast_node,
    edit_document_section,
    extract_hyperedge_exports,
    sync_hypergraph_matrix,
)
from adk.tools.building.template_manager import (
    detect_template_from_prompt,
    prompt_user_for_template,
    resolve_template_name,
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
    scout_domain_conventions,
    select_model_tier,
    synthesize_table_of_contents,
)
from adk.tools.verification import compile_symbolic_references, iter_workspace_python_files, run_isolated_tests


def _merge_bibtex_entries(existing_bib: str, new_bib: str) -> str:
    """Merge BibTeX entries from existing_bib and new_bib, deduplicating by citation key while preserving order."""
    entry_pattern = re.compile(r"(@\w+\s*\{\s*([^,\s]+)\s*,.*?\n\})", re.DOTALL)
    entries_by_key: dict[str, str] = {}
    ordered_keys: list[str] = []

    for source_text in (existing_bib, new_bib):
        if not source_text or not source_text.strip():
            continue
        matches = list(entry_pattern.finditer(source_text))
        if matches:
            for m in matches:
                full_entry = m.group(1).strip()
                cite_key = m.group(2).strip()
                if cite_key not in entries_by_key:
                    ordered_keys.append(cite_key)
                entries_by_key[cite_key] = full_entry
        else:
            raw_key = f"_raw_{len(ordered_keys)}"
            ordered_keys.append(raw_key)
            entries_by_key[raw_key] = source_text.strip()

    return "\n\n".join(entries_by_key[k] for k in ordered_keys) + "\n"


def _issue_signature(report: dict[str, Any]) -> str:
    """Stable identity of a verification failure. The same text twice means the repair did not move."""
    issues = report.get("issues") or []
    if not isinstance(issues, list):
        issues = [issues]
    lines = sorted(str(item).strip() for item in issues if str(item).strip())
    return "\n".join(lines)



class NeuroSymbolicOrchestrator:
    """Main control loop for the Python-only Neuro-Symbolic Harness."""

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
        is_mock_mode = self.provider == "mock"

        def _normalize_raw_code(raw_text: str | None) -> str | None:
            if not isinstance(raw_text, str) or not raw_text.strip():
                return raw_text
            # If LLM emitted single-line JSON string with literal \n escapes instead of real newlines, normalize it
            if "\\n" in raw_text and ("\n" not in raw_text.strip() or raw_text.count("\\n") > raw_text.count("\n") * 2):
                return raw_text.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
            return raw_text

        # 1. AST-level edits (from seed_coder or dynamic coding specialists)
        custom_edits = llm_output.get("ast_edits")
        if isinstance(custom_edits, list) and custom_edits:
            for item in custom_edits:
                if not isinstance(item, dict):
                    continue
                sym = item.get("symbol") or item.get("name") or item.get("target")
                code_str = item.get("code") or item.get("content") or item.get("value")
                if not sym or code_str is None:
                    continue
                code_str = _normalize_raw_code(str(code_str))
                target_rel = item.get("file") or node_path
                target_py = self.workspace_dir / target_rel
                edit_ast_node(target_py, str(sym), str(code_str))
                materialized_any = True

        # 2. Full module source_code (if provided alongside or instead of ast_edits)
        action_code_obj = llm_output.get("action_code") if isinstance(llm_output.get("action_code"), dict) else {}
        payload_obj = llm_output.get("payload") if isinstance(llm_output.get("payload"), dict) else {}
        agent_obj = llm_output.get("agent") if isinstance(llm_output.get("agent"), dict) else {}
        artifact_obj = llm_output.get("artifact") if isinstance(llm_output.get("artifact"), dict) else {}
        files_list = llm_output.get("files") if isinstance(llm_output.get("files"), list) else []
        for f_item in files_list:
            if isinstance(f_item, dict):
                f_name = str(f_item.get("filename") or f_item.get("file") or f_item.get("path") or "").strip()
                f_body = f_item.get("content") or f_item.get("code") or f_item.get("source_code")
                if f_name and isinstance(f_body, str) and f_body.strip():
                    f_body = _normalize_raw_code(f_body)
                    try:
                        p_cand = Path(f_name)
                        if p_cand.is_absolute():
                            try:
                                clean_rel = p_cand.relative_to(self.workspace_dir)
                            except ValueError:
                                clean_rel = Path(p_cand.name)
                        else:
                            clean_rel = p_cand
                    except Exception:
                        clean_rel = Path(Path(f_name).name)
                    f_dest = (self.workspace_dir / clean_rel).resolve()
                    if str(f_dest).startswith(str(self.workspace_dir.resolve())):
                        f_dest.parent.mkdir(parents=True, exist_ok=True)
                        f_dest.write_text(f_body, encoding="utf-8")
                        materialized_any = True

        source_code = (
            llm_output.get("source_code")
            or llm_output.get("code")
            or llm_output.get("python_code")
            or action_code_obj.get("code")
            or agent_obj.get("code")
            or artifact_obj.get("code")
            or (llm_output.get("content") if node_path.endswith(".py") else None)
            or (payload_obj.get("content") if node_path.endswith(".py") else None)
            or (agent_obj.get("content") if node_path.endswith(".py") else None)
            or (artifact_obj.get("content") if node_path.endswith(".py") else None)
        )
        source_code = _normalize_raw_code(source_code)
        if isinstance(source_code, str) and source_code.strip() and node_path.endswith(".py") and not materialized_any:
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            full_file_path.write_text(source_code, encoding="utf-8")
            materialized_any = True

        # 3. Unit test suite (from seed_tester or split testing sub-agents)
        test_code = _normalize_raw_code(llm_output.get("test_code"))
        if isinstance(test_code, str) and test_code.strip():
            test_rel = str(llm_output.get("test_file") or "test_core.py")
            test_path = self.workspace_dir / test_rel
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(test_code, encoding="utf-8")
            materialized_any = True

        # 4. Empirical benchmark CSV data (from seed_tester)
        params_obj = llm_output.get("parameters") if isinstance(llm_output.get("parameters"), dict) else {}
        csv_content = llm_output.get("csv_content") or (
            params_obj.get("content") if str(params_obj.get("file_path", "")).endswith(".csv") else None
        )
        if isinstance(csv_content, str) and csv_content.strip():
            csv_rel = str(llm_output.get("benchmark_file") or params_obj.get("file_path") or "results.csv")
            csv_path = self.workspace_dir / csv_rel
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            csv_path.write_text(csv_content, encoding="utf-8")
            now = time.time() + 1.0
            os.utime(csv_path, (now, now))
            materialized_any = True

        # 5. Vector plotting script (from seed_tester)
        plot_script = _normalize_raw_code(llm_output.get("plot_script"))
        if isinstance(plot_script, str) and plot_script.strip():
            plot_rel = str(llm_output.get("plot_file") or "plot_results.py")
            plot_path = self.workspace_dir / plot_rel
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            plot_path.write_text(plot_script, encoding="utf-8")
            materialized_any = True

        # 6. BibTeX bibliography & Literature review (background_researcher, discoverer_researcher, sota_researcher)
        research_stage = str(llm_output.get("research_stage") or "").strip().lower()
        bibtex_entries = llm_output.get("bibtex_entries")
        if isinstance(bibtex_entries, str) and bibtex_entries.strip():
            bib_rel = str(llm_output.get("bib_file") or "references.bib")
            bib_path = self.workspace_dir / bib_rel
            bib_path.parent.mkdir(parents=True, exist_ok=True)
            if bib_path.exists():
                existing_bib = bib_path.read_text(encoding="utf-8", errors="ignore")
                merged_bib = _merge_bibtex_entries(existing_bib, bibtex_entries)
                bib_path.write_text(merged_bib, encoding="utf-8")
            else:
                bib_path.write_text(bibtex_entries.strip() + "\n", encoding="utf-8")
            materialized_any = True

        # Catch any BibTeX entries embedded in code, ast_edits or action fields
        raw_output_text = str(llm_output)
        if "@article{" in raw_output_text or "@book{" in raw_output_text or "@inproceedings{" in raw_output_text:
            extracted_entries = re.findall(
                r"(@\w+\s*\{[^{}]*\{[^{}]*\}[^{}]*\}|@\w+\s*\{[^@\n]+\n(?:[ \t]+[^@\n]+\n)*\})",
                raw_output_text,
            )
            if extracted_entries:
                stray_bib_str = "\n\n".join(extracted_entries)
                bib_p = self.workspace_dir / "references.bib"
                bib_p.parent.mkdir(parents=True, exist_ok=True)
                if bib_p.exists():
                    ex_b = bib_p.read_text(encoding="utf-8", errors="ignore")
                    bib_p.write_text(_merge_bibtex_entries(ex_b, stray_bib_str), encoding="utf-8")
                else:
                    bib_p.write_text(stray_bib_str.strip() + "\n", encoding="utf-8")

        lit_section = llm_output.get("literature_review_section")
        if isinstance(lit_section, str) and lit_section.strip() and self.include_docs:
            doc_target = full_file_path if node_path.endswith((".md", ".tex")) else (self.workspace_dir / "thesis.md")
            sec_title = str(llm_output.get("section_title") or "Analiza Stanu Wiedzy (SOTA)")
            if research_stage == "discoverer" and doc_target.exists():
                existing_doc = doc_target.read_text(encoding="utf-8", errors="ignore")
                sec_pattern = re.compile(
                    rf"^##+\s+{re.escape(sec_title)}\s*$(.*?)(?=^##\s+|\Z)",
                    re.MULTILINE | re.DOTALL,
                )
                m_sec = sec_pattern.search(existing_doc)
                if m_sec and lit_section.strip() not in m_sec.group(1):
                    combined_lit = m_sec.group(1).strip() + "\n\n" + lit_section.strip()
                    edit_document_section(doc_target, sec_title, combined_lit)
                else:
                    edit_document_section(doc_target, sec_title, lit_section)
            else:
                edit_document_section(doc_target, sec_title, lit_section)
            materialized_any = True

        # 7. Thesis subsections (from seed_writer)
        if self.include_docs:
            doc_target = full_file_path if node_path.endswith((".md", ".tex")) else (self.workspace_dir / "thesis.md")

            # Check if model output a structured chapter with a title and subsections
            ch_title = (
                llm_output.get("chapter_title")
                or llm_output.get("chapter_name")
                or (llm_output.get("chapter", {}).get("title") if isinstance(llm_output.get("chapter"), dict) else None)
            )
            raw_subs = (
                llm_output.get("sections")
                or llm_output.get("subsections")
                or (llm_output.get("chapter", {}).get("sections") if isinstance(llm_output.get("chapter"), dict) else None)
            )
            if ch_title and isinstance(raw_subs, list) and raw_subs:
                acc_subs: list[str] = []
                for s in raw_subs:
                    if isinstance(s, dict):
                        st = s.get("title") or s.get("section_title") or s.get("heading") or ""
                        sc = s.get("content") or s.get("section_content") or s.get("text") or s.get("body") or ""
                        if st and sc:
                            acc_subs.append(f"### {st}\n{sc}")
                        elif sc:
                            acc_subs.append(str(sc))
                if acc_subs:
                    edit_document_section(doc_target, str(ch_title), "\n\n".join(acc_subs))
                    materialized_any = True

            def _extract_chapter_dict_body(ch_dict: dict[str, Any]) -> str:
                parts_acc: list[str] = []
                top_text = (
                    ch_dict.get("section_content")
                    or ch_dict.get("content")
                    or ch_dict.get("body")
                    or ch_dict.get("text")
                    or ch_dict.get("summary")
                    or ch_dict.get("focus")
                )
                if isinstance(top_text, str) and top_text.strip():
                    parts_acc.append(top_text.strip())
                elif isinstance(top_text, list):
                    for item in top_text:
                        if isinstance(item, dict):
                            ih = item.get("heading") or item.get("title")
                            ic = item.get("content") or item.get("text") or item.get("body") or item.get("focus")
                            if ih and ic:
                                parts_acc.append(f"### {ih}\n{ic}")
                            elif ic:
                                parts_acc.append(str(ic))
                sub_items = (
                    ch_dict.get("subsections")
                    or ch_dict.get("sections")
                    or ch_dict.get("structure")
                    or []
                )
                if isinstance(sub_items, list):
                    for sub in sub_items:
                        if isinstance(sub, dict):
                            sub_h = sub.get("heading") or sub.get("title")
                            sub_c = (
                                sub.get("content")
                                or sub.get("text")
                                or sub.get("body")
                                or sub.get("summary")
                                or sub.get("focus")
                            )
                            if sub_h and sub_c:
                                parts_acc.append(f"### {sub_h}\n{sub_c}")
                            elif sub_c:
                                parts_acc.append(str(sub_c))
                return "\n\n".join(parts_acc).strip()

            thesis_struct = llm_output.get("thesis_structure") if isinstance(llm_output.get("thesis_structure"), dict) else {}
            sections_list = (
                llm_output.get("sections")
                or llm_output.get("chapters")
                or thesis_struct.get("chapters")
            )
            if isinstance(sections_list, list) and sections_list:
                for sec in sections_list:
                    if isinstance(sec, dict):
                        s_title = sec.get("section_title") or sec.get("title") or sec.get("heading")
                        s_body = _extract_chapter_dict_body(sec)
                        if s_title and s_body:
                            edit_document_section(doc_target, str(s_title), str(s_body))
                            materialized_any = True

            if not materialized_any:
                chapter_candidates: list[dict[str, Any]] = []
                if isinstance(llm_output.get("chapter"), dict):
                    chapter_candidates.append(llm_output["chapter"])
                for k, v in llm_output.items():
                    if isinstance(v, dict) and (
                        k.startswith("chapter_")
                        or k.startswith("thesis_chapter_")
                        or k == "chapter_analysis"
                    ):
                        chapter_candidates.append(v)
                for ch_obj in chapter_candidates:
                    c_title = str(ch_obj.get("title") or ch_obj.get("section_title") or "Rozdział Pracy")
                    c_body = _extract_chapter_dict_body(ch_obj)
                    if c_body:
                        edit_document_section(doc_target, c_title, c_body)
                        materialized_any = True

            if not materialized_any and llm_output.get("section_title") and llm_output.get("section_content"):
                edit_document_section(
                    doc_target,
                    str(llm_output["section_title"]),
                    str(llm_output["section_content"]),
                )
                materialized_any = True
            elif node_path.endswith((".md", ".tex")) and not materialized_any:
                raw_doc_str = (
                    llm_output.get("content")
                    or llm_output.get("markdown")
                    or llm_output.get("text")
                    or llm_output.get("summary")
                    or payload_obj.get("content")
                )
                if isinstance(raw_doc_str, str) and raw_doc_str.strip():
                    stripped_raw = raw_doc_str.strip()
                    if stripped_raw.startswith(("{", "[")):
                        parsed_json = None
                        try:
                            parsed_json = json.loads(stripped_raw)
                        except Exception:
                            from adk.core.llm import _extract_json_from_text
                            extracted = _extract_json_from_text(stripped_raw)
                            if isinstance(extracted, dict):
                                parsed_json = extracted
                        if isinstance(parsed_json, dict):
                            p_sections = parsed_json.get("sections") or parsed_json.get("chapters")
                            p_title = parsed_json.get("chapter_title") or parsed_json.get("title") or "Rozdział Pracy"
                            if isinstance(p_sections, list) and p_sections:
                                acc: list[str] = []
                                for s in p_sections:
                                    if isinstance(s, dict):
                                        st = s.get("title") or s.get("heading") or ""
                                        sc = s.get("content") or s.get("text") or s.get("body") or ""
                                        if st and sc:
                                            acc.append(f"### {st}\n{sc}")
                                        elif sc:
                                            acc.append(str(sc))
                                if acc:
                                    edit_document_section(doc_target, str(p_title), "\n\n".join(acc))
                                    materialized_any = True
                    else:
                        sec_t = str(llm_output.get("title") or llm_output.get("section_title") or "Sekcja Dokumentacji")
                        edit_document_section(doc_target, sec_t, stripped_raw)
                        materialized_any = True

        # 8. Offline Mock Fallback ONLY when provider is mock/None (NEVER in live LLM runs!)
        if is_mock_mode:
            from adk.mocks.code_fixtures import (
                TICTACTOE_CONFIG_AST_NODES,
                TICTACTOE_CORE_CODE,
                TICTACTOE_DOC_SECTION_CONTENT,
                TICTACTOE_DOC_SECTION_TITLE,
                TICTACTOE_INITIAL_CSV,
                TICTACTOE_TEST_CODE,
            )

            if self.include_docs and (node_path.endswith((".md", ".tex")) or materialized_any):
                csv_path = self.workspace_dir / "results.csv"
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                if not csv_path.exists():
                    csv_path.write_text(TICTACTOE_INITIAL_CSV, encoding="utf-8")
                now = time.time() + 1.0
                os.utime(csv_path, (now, now))

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
        agent_id = self._resolve_active_agent(task.get("assigned_agent"), fallback="seed_coder")
        task["assigned_agent"] = agent_id

        agent_meta = registry.get(agent_id, {})
        agent_md = self.adk_root / agent_meta.get("path", f"agents/building/{agent_id}.md")
        if not agent_md.exists():
            agent_md = self.adk_root / "agents" / "building" / "seed_coder.md"

        matrix_data = read_json_state(self.matrix_path)
        raw_node_id = task.get("target_node", "v1")
        node_id, node_path = self._resolve_target_node(raw_node_id, task=task, fallback="v1")
        task["target_node"] = node_id
        full_target = self.workspace_dir / node_path
        existing_content = full_target.read_text(encoding="utf-8") if full_target.exists() else ""

        # Avoid dumping 30+ KB document history into LLM prompt; pass outline + target chapter/tail for context
        if node_path.endswith((".md", ".tex")) and len(existing_content) > 1500:
            from adk.tools.building.doc_editor import _extract_canonical_chapter_num

            lines = existing_content.splitlines()
            outline_lines = [
                line for line in lines
                if line.strip().startswith(("#", "\\chapter", "\\section", "\\subsection"))
            ]
            outline_str = "\n".join(outline_lines[:30])
            task_desc_str = str(task.get("description", ""))
            target_ch = _extract_canonical_chapter_num(task_desc_str)
            target_excerpt = ""
            if target_ch is not None and node_path.endswith(".md"):
                ch_matches = list(re.finditer(r"^##\s+([^\n]+)$", existing_content, flags=re.MULTILINE))
                for i, cm in enumerate(ch_matches):
                    if _extract_canonical_chapter_num(cm.group(1)) == target_ch:
                        c_start = cm.start()
                        c_end = ch_matches[i + 1].start() if i + 1 < len(ch_matches) else len(existing_content)
                        target_excerpt = existing_content[c_start:c_end].strip()[:1500]
                        break
            tail_str = target_excerpt if target_excerpt else existing_content[-600:]
            context_label = (
                f"[CURRENT CONTENT OF CHAPTER {target_ch}]:"
                if target_excerpt
                else "[LAST 600 CHARACTERS OF DOCUMENT]:"
            )
            payload_existing_content = (
                f"[DOCUMENT OUTLINE (headings)]:\n{outline_str}\n\n"
                f"{context_label}\n{tail_str}"
            )
        else:
            payload_existing_content = existing_content

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

        blueprint_data = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        recon_data = blueprint_data.get("literature_recon", {}) if isinstance(blueprint_data, dict) else {}
        is_doc_or_research_agent = (
            node_id == "v4"
            or node_path.endswith((".md", ".tex", ".bib"))
            or agent_id in ("seed_writer", "background_researcher", "discoverer_researcher", "sota_researcher")
        )

        builder_payload: dict[str, Any] = {
            "user_prompt": self.current_user_prompt,
            "task": task,
            "target_file": node_path,
            "existing_content": payload_existing_content,
            "exports": exports_info.get("exports", {}),
            "csv_schemas": exports_info.get("csv_schemas", {}),
            "hypergraph_nodes": scoped_graph.get("nodes", {}),
            "active_edges": scoped_graph.get("active_edges", {}),
            "grounded_hypergraph_state": grounded_state,
            "standard_metrics": recon_data.get("standard_metrics", []),
            "canonical_baselines": recon_data.get("canonical_baselines", []),
        }
        if is_doc_or_research_agent:
            builder_payload["thesis_type"] = blueprint_data.get("thesis_type", "inzynierska")
            builder_payload["template_name"] = blueprint_data.get("template_name", "thesis_plodz")
            builder_payload["table_of_contents"] = blueprint_data.get("table_of_contents", {})
            builder_payload["available_citation_keys"] = recon_data.get("available_citation_keys", [])
            builder_payload["sampled_methodologies"] = recon_data.get("sampled_methodologies", [])

        llm_res = call_agent(
            agent_md,
            builder_payload,
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
                if not p.is_file() or "__pycache__" in p.parts or p.name == ".gitkeep":
                    continue
                rel_parts = p.relative_to(self.workspace_dir).parts
                if "benchmarks" in rel_parts or ".git" in rel_parts:
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
                if t_node in ("v1", "v2"):
                    pending.update({"config.py", "core.py"})
                elif t_node in ("v3", "v5"):
                    pending.update({"results.csv", "figures", "plot_results.py", "test_core.py"})
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
        matrix_data = read_json_state(self.matrix_path)
        matrix_nodes: dict[str, Any] = matrix_data.get("nodes", {})
        matrix_inc: dict[str, dict[str, int]] = matrix_data.get("matrix", {})

        raw_target_node = str(current_task.get("target_node", "v1"))
        target_node, node_path = self._resolve_target_node(raw_target_node, task=current_task, fallback="v1")
        current_task["target_node"] = target_node
        node_meta = matrix_nodes.get(target_node, {})
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

        # Only attach experiment errors to tasks that actually govern experiments/data (e.g. results.csv)
        if self._last_experiment_error and is_data_scope:
            experiment_err = self._last_experiment_error[:4000]
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

            if not is_final_gate:
                redteam_audit = {
                    "status": "SKIPPED_INTERMEDIATE_TASK",
                    "verdict": "PASS",
                    "gate_3_approved": False,
                    "issues": [],
                }
            else:
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

        def _extract_agent_str(val: Any, default_id: str) -> str:
            if isinstance(val, dict):
                val = val.get("agent_id") or val.get("name") or val.get("agent") or val.get("id") or default_id
            s = str(val or default_id).strip()
            if not s or any(ch in s for ch in ("{", "}", ":", "'", '"', "/", "\\", " ")):
                return default_id
            return s

        # Defensive normalization of LLM keys
        if isinstance(decision_out, dict):
            if "decision" in decision_out and "action" not in decision_out:
                decision_out["action"] = decision_out["decision"]
            if "agent" in decision_out and "agent_id" not in decision_out:
                decision_out["agent_id"] = _extract_agent_str(decision_out["agent"], failed_agent)
            elif "agent_id" in decision_out:
                decision_out["agent_id"] = _extract_agent_str(decision_out["agent_id"], failed_agent)
            if "injected_rule" in decision_out and "rule" not in decision_out:
                decision_out["rule"] = decision_out["injected_rule"]
            elif "suggested_rule" in decision_out and "rule" not in decision_out:
                decision_out["rule"] = decision_out["suggested_rule"]

        action = str(decision_out.get("action") or decision_out.get("decision") or "MUTATE_AGENT")

        if action in ("INSTALL_DEPENDENCY", "INSTALL_PACKAGE"):
            from adk.tools.evolution.dependency_manager import install_package

            pkg_name = str(decision_out.get("package_name") or decision_out.get("package") or "").strip()
            if not pkg_name:
                val_rep = payload.get("validation_report") or {}
                for issue in val_rep.get("issues", []):
                    m = re.search(r"No module named ['\"]([^'\"]+)['\"]", str(issue))
                    if m:
                        pkg_name = m.group(1)
                        break
            if pkg_name:
                pkg_map = {"sklearn": "scikit-learn", "cv2": "opencv-python", "PIL": "pillow"}
                pkg_to_install = pkg_map.get(pkg_name, pkg_name)
                inst_res = install_package(pkg_to_install)
                self._record_evolution_event({"type": "DEPENDENCY_INSTALLED", "details": inst_res})
                return {"action": "INSTALL_DEPENDENCY", "decision": "INSTALL_DEPENDENCY", "details": inst_res}

        # Proactive self-healing fallback for missing modules
        val_rep = payload.get("validation_report") or {}
        for issue in val_rep.get("issues", []):
            m = re.search(r"No module named ['\"]([^'\"]+)['\"]", str(issue))
            if m:
                missing_mod = m.group(1)
                pkg_map = {"sklearn": "scikit-learn", "cv2": "opencv-python", "PIL": "pillow"}
                pkg_to_install = pkg_map.get(missing_mod, missing_mod)
                from adk.tools.evolution.dependency_manager import install_package
                inst_res = install_package(pkg_to_install)
                self._record_evolution_event({"type": "AUTO_DEPENDENCY_INSTALLED", "details": inst_res})
                break

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
            raw_spec = (
                decision_out.get("specialization")
                or enriched_payload.get("missing_specialization")
                or "custom_specialist"
            )
            if isinstance(raw_spec, dict):
                raw_spec = raw_spec.get("specialization") or raw_spec.get("name") or "custom_specialist"
            spec = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw_spec)).strip("_").lower() or "custom_specialist"
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
            raw_split_target = _extract_agent_str(
                decision_out.get("agent_id") or enriched_payload.get("split_agent_id"),
                failed_agent,
            )
            target_agent = self._resolve_active_agent(raw_split_target, fallback=failed_agent)
            raw_sub_specs = decision_out.get("sub_specializations") or enriched_payload.get(
                "sub_specializations", ("unit_testing", "edge_case_testing")
            )
            if isinstance(raw_sub_specs, (list, tuple)) and len(raw_sub_specs) >= 2:
                clean_subs = []
                for idx_s, s_item in enumerate(raw_sub_specs[:2]):
                    if isinstance(s_item, dict):
                        s_item = s_item.get("name") or s_item.get("specialization") or f"sub_{idx_s + 1}"
                    clean_s = re.sub(r"[^a-zA-Z0-9_]", "_", str(s_item)).strip("_").lower() or f"sub_{idx_s + 1}"
                    clean_subs.append(clean_s)
                sub_specs: tuple[str, ...] | list[str] = clean_subs
            else:
                sub_specs = ("unit_testing", "edge_case_testing")
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

        target_mut_agent = _extract_agent_str(decision_out.get("agent_id"), failed_agent)
        # Gwarancja zgodności ze stanem hipergrafu: cel mutacji musi dyscyplinować agenta, który faktycznie zawiódł
        if failed_agent and target_mut_agent != failed_agent:
            if target_mut_agent in ("seed_coder", "unknown", "") and failed_agent != "seed_coder":
                target_mut_agent = failed_agent
        registry = read_json_state(self.registry_path).get("agents", {})
        if target_mut_agent not in registry and target_mut_agent != "task_planner":
            target_mut_agent = self._resolve_active_agent(target_mut_agent, fallback=failed_agent)
        elif target_mut_agent in registry and not registry[target_mut_agent].get("active", True):
            for cand_id, cand_meta in registry.items():
                if cand_meta.get("parent_agent") == target_mut_agent and cand_meta.get("active", True):
                    target_mut_agent = cand_id
                    break

        rel_md = registry.get(target_mut_agent, {}).get("path", f"agents/building/{target_mut_agent}.md")
        target_md_path = self.adk_root / rel_md
        if not target_md_path.exists():
            alt_planning = self.adk_root / "agents" / "planning" / f"{target_mut_agent}.md"
            if alt_planning.exists():
                target_md_path = alt_planning
            else:
                fallback_ag = self._resolve_active_agent(failed_agent, fallback="seed_coder")
                fallback_rel = registry.get(fallback_ag, {}).get("path", "agents/building/seed_coder.md")
                target_md_path = self.adk_root / fallback_rel
                if not target_md_path.exists():
                    target_md_path = self.adk_root / "agents" / "building" / "seed_coder.md"

        raw_rule = decision_out.get(
            "rule",
            "Always preserve AST signature compatibility and symbolic pointer validity.",
        )
        if isinstance(raw_rule, (dict, list)):
            raw_rule = json.dumps(raw_rule, ensure_ascii=False)

        mut_res = mutate_agent_prompt(
            agent_md_path=target_md_path,
            new_rule=str(raw_rule),
            failure_context=json.dumps(payload, ensure_ascii=False),
            failure_ledger_path=self.failure_ledger_path,
            provider=self.provider,
        )
        self._record_evolution_event({"type": "AGENT_MUTATED", "details": mut_res})
        if mut_res.get("compacted"):
            self._record_evolution_event({"type": "PROMPT_CONSOLIDATED", "details": mut_res["compaction_details"]})
        return {"action": "MUTATE_AGENT", "decision": "MUTATE_AGENT", "details": mut_res}

    def _resolve_active_agent(self, preferred: Any, fallback: str = "seed_coder") -> str:
        """Resolve an agent ID to an active registered agent (handling split parent agents, dict payloads, or unknown LLM names)."""
        if isinstance(preferred, dict):
            preferred = preferred.get("agent_id") or preferred.get("name") or preferred.get("agent") or preferred.get("id") or ""
        pref_str = str(preferred or "").strip()
        if any(ch in pref_str for ch in ("{", "}", ":", "'", '"', "/", "\\", " ")):
            pref_str = ""

        reg_agents = (
            read_json_state(self.registry_path).get("agents", {})
            if self.registry_path.exists()
            else {}
        )
        if pref_str in reg_agents:
            if reg_agents[pref_str].get("active", True):
                return pref_str
            for cand_id, cand_meta in reg_agents.items():
                if cand_meta.get("parent_agent") == pref_str and cand_meta.get("active", True):
                    return cand_id
        if fallback in reg_agents:
            if reg_agents[fallback].get("active", True):
                return fallback
            for cand_id, cand_meta in reg_agents.items():
                if cand_meta.get("parent_agent") == fallback and cand_meta.get("active", True):
                    return cand_id
        for cand_id, cand_meta in reg_agents.items():
            if cand_meta.get("active", True) and (
                cand_meta.get("domain") == "building" or cand_meta.get("layer") == "building"
            ):
                return cand_id
        return pref_str or fallback or "seed_coder"

    def _resolve_target_node(
        self,
        node_id: Any,
        task: dict[str, Any] | None = None,
        fallback: str = "v1",
    ) -> tuple[str, str]:
        """Resolve arbitrary or hallucinated node identifiers (e.g. 'v7', 'core.py') to a valid hypergraph node and path."""
        matrix_data = read_json_state(self.matrix_path)
        nodes: dict[str, Any] = matrix_data.get("nodes", {})

        raw_id = str(node_id or "").strip()
        # 1. Direct hit in nodes
        if raw_id in nodes:
            return raw_id, str(nodes[raw_id].get("path", raw_id))

        # 2. Check if raw_id is a file path matching any node's path or filename
        for n_id, n_meta in nodes.items():
            n_path = str(n_meta.get("path", ""))
            if n_path == raw_id or Path(n_path).name == Path(raw_id).name:
                return n_id, n_path

        # 3. Check task metadata (target_file, file, or description) for mention of known files
        if task:
            target_f = str(task.get("target_file") or task.get("file") or "").strip()
            desc = str(task.get("description", "")).strip().lower()
            for n_id, n_meta in nodes.items():
                n_path = str(n_meta.get("path", ""))
                fname = Path(n_path).name.lower()
                if (target_f and (n_path == target_f or fname == Path(target_f).name.lower())) or (
                    fname in desc or n_path.lower() in desc
                ):
                    return n_id, n_path

        # 4. If fallback node exists in nodes, use it
        if fallback in nodes:
            return fallback, str(nodes[fallback].get("path", fallback))

        # 5. Fallback to first available node in hypergraph, or default v1 / config.py
        if nodes:
            first_id = next(iter(nodes))
            return first_id, str(nodes[first_id].get("path", first_id))

        return "v1", "config.py"

    def _normalize_and_heal_task_plan(
        self,
        raw_tasks: list[dict[str, Any]],
        blast: dict[str, Any],
        user_prompt: str,
        multi_cycle_waves: bool = False,
        preferred_coder: str | None = None,
        thesis_type: str | None = None,
        planned_chapters: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Ensure all hypergraph blast-radius nodes and active agents are valid while preserving elastic task counts."""
        coder_agent = self._resolve_active_agent(preferred_coder or "seed_coder", fallback="seed_coder")
        tester_agent = self._resolve_active_agent("seed_tester", fallback="seed_coder")
        sota_agent = self._resolve_active_agent("sota_researcher", fallback="seed_writer")
        bg_agent = self._resolve_active_agent("background_researcher", fallback=sota_agent)
        disc_agent = self._resolve_active_agent("discoverer_researcher", fallback=sota_agent)
        writer_agent = self._resolve_active_agent("seed_writer", fallback="seed_coder")

        spec_to_agent = {
            "python_coding": coder_agent,
            "coding": coder_agent,
            "unit_testing": tester_agent,
            "testing": tester_agent,
            "academic_writing": writer_agent,
            "writing": writer_agent,
            "background_literature": bg_agent,
            "literature_review": sota_agent,
            "sota_discovery": disc_agent,
        }

        # Flatten nested subtasks if planner emits hierarchical task decompositions
        flattened_raw: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_tasks or []):
            if not isinstance(item, dict):
                continue
            subtasks = item.get("subtasks")
            if isinstance(subtasks, list) and subtasks:
                parent_id = str(item.get("task_id") or item.get("id") or f"T{idx + 1}")
                parent_node = item.get("target_node") or item.get("node_id") or item.get("node")
                parent_agent = item.get("assigned_agent") or item.get("agent")
                parent_desc = item.get("description", "")
                for sub_idx, sub in enumerate(subtasks, 1):
                    if isinstance(sub, dict):
                        sub_dict = dict(sub)
                        if "task_id" not in sub_dict and "id" not in sub_dict:
                            sub_dict["task_id"] = f"{parent_id}.{sub_idx}"
                        if not sub_dict.get("target_node") and not sub_dict.get("node_id") and parent_node:
                            sub_dict["target_node"] = parent_node
                        if not sub_dict.get("assigned_agent") and not sub_dict.get("agent") and parent_agent:
                            sub_dict["assigned_agent"] = parent_agent
                        if parent_desc and parent_desc not in str(sub_dict.get("description", "")):
                            sub_dict["description"] = f"[{parent_id}] {sub_dict.get('description', '')}"
                        flattened_raw.append(sub_dict)
            else:
                flattened_raw.append(item)

        cleaned: list[dict[str, Any]] = []
        for idx, item in enumerate(flattened_raw):
            if not isinstance(item, dict):
                continue
            t_id = str(item.get("task_id") or item.get("id") or f"T{idx + 1}")
            desc_str = str(item.get("description") or "")
            hg_nodes = item.get("hypergraph_nodes") or item.get("nodes") or []
            first_hg_node = str(hg_nodes[0]) if isinstance(hg_nodes, list) and hg_nodes else ""
            out_files = item.get("output_files") or []
            first_out_file = str(out_files[0]).lower() if isinstance(out_files, list) and out_files else str(item.get("target_file") or item.get("file") or "").lower()

            node_id = str(item.get("target_node") or item.get("node_id") or item.get("node") or first_hg_node or "")
            if node_id not in ("v1", "v2", "v3", "v4", "v5"):
                hint_text = f"{first_out_file} {desc_str.lower()}"
                if "config.py" in hint_text:
                    node_id = "v1"
                elif "test_core.py" in hint_text or "pytest" in hint_text or "unit test" in hint_text:
                    node_id = "v5"
                elif "results.csv" in hint_text or "plot_results.py" in hint_text:
                    node_id = "v3"
                elif "core.py" in hint_text:
                    node_id = "v2"
                elif "thesis.md" in hint_text or "references.bib" in hint_text or "rozdział" in hint_text:
                    node_id = "v4"
                else:
                    node_id = "v1"

            raw_agents_list = item.get("agents")
            raw_first_ag = raw_agents_list[0] if isinstance(raw_agents_list, list) and raw_agents_list else ""
            raw_ag = str(
                item.get("assigned_agent")
                or item.get("agent")
                or item.get("agent_name")
                or item.get("agent_id")
                or raw_first_ag
                or spec_to_agent.get(str(item.get("agent_specialization") or "").strip().lower(), "")
            )
            default_ag = (
                writer_agent
                if node_id == "v4"
                else (tester_agent if node_id in ("v3", "v5") else coder_agent)
            )
            ag = self._resolve_active_agent(raw_ag, fallback=default_ag)
            cleaned.append(
                {
                    "task_id": t_id,
                    "description": desc_str or f"Realizacja węzła {node_id}",
                    "target_node": node_id,
                    "assigned_agent": ag,
                    "status": "TODO",
                }
            )

        t_type = (thesis_type or "inzynierska").strip().lower()
        is_paper = t_type in ("paper", "article", "scientific_paper")

        # Build map of custom chapter titles from planned_chapters if provided
        custom_ch_titles: dict[int, str] = {}
        for idx_pc, pc in enumerate(planned_chapters or [], 1):
            if isinstance(pc, dict):
                ch_num = int(pc.get("index") or pc.get("chapter_index") or pc.get("id") or idx_pc)
                ch_t = str(pc.get("title") or pc.get("chapter_title") or "").strip()
                if ch_t:
                    custom_ch_titles[ch_num] = ch_t
            elif isinstance(pc, str) and pc.strip():
                custom_ch_titles[idx_pc] = pc.strip()

        # Inspect which chapters are covered by v4 tasks in cleaned
        v4_tasks = [t for t in cleaned if t.get("target_node") == "v4"]
        covered_chapters: set[int] = set()
        for vt in v4_tasks:
            desc_l = str(vt.get("description", "")).lower()
            if self.provider == "mock" and any(
                w in desc_l for w in ("all 6 chapters", "wszystkie 6 rozdział", "6 chapters", "planned_chapters")
            ):
                covered_chapters.update(range(1, 7))
            for ch_i in range(1, 7):
                if (
                    re.search(
                        rf"\b(?:podrozdzia[łl]u?|rozdzia[łl]u?|chapter|sekcj[ai]|section|ch|r0?)\s*{ch_i}(?:\.\d+|\b)",
                        desc_l,
                    )
                    or re.search(rf"\b{ch_i}\.\d+\b", desc_l)
                ):
                    covered_chapters.add(ch_i)
                if ch_i in custom_ch_titles and custom_ch_titles[ch_i].lower()[:18] in desc_l:
                    covered_chapters.add(ch_i)
            if any(w in desc_l for w in ("wstęp", "wstep", "cel", "teza", "intro", "problem")):
                covered_chapters.add(1)
            if any(w in desc_l for w in ("sota", "stan wiedzy", "literatur", "przegląd", "przeglad", "related", "background")):
                covered_chapters.add(2)
            if any(w in desc_l for w in ("architektur", "formalizm", "matematyczn", "system", "design", "model", "tikz")):
                covered_chapters.add(3)
            if any(w in desc_l for w in ("implementacj", "algorytm", "struktury", "implementation", "ast")):
                covered_chapters.add(4)
            if any(w in desc_l for w in ("wyniki", "ewaluacj", "eksperyment", "badani", "evaluation", "metodologia", "empirical", "results")):
                covered_chapters.add(5)
            if any(w in desc_l for w in ("podsumowan", "wnioski", "conclusi", "kierunki", "summary")):
                covered_chapters.add(6)

        # Only synthesize a full baseline pipeline from scratch if cleaned is completely empty.
        # Whenever task_planner returns tasks (whether 5, 10, 15, or 25+), preserve them elastically!
        needs_full_multi_cycle = multi_cycle_waves and not cleaned

        if needs_full_multi_cycle:
            # Build an incremental Vertical Feature Slice pipeline:
            # Code development, unit tests, and thesis documentation progress together feature by feature,
            # with guaranteed coverage of all canonical thesis chapters.
            multi_tasks: list[dict[str, Any]] = []

            # Slice 1: Domain Assumptions, Literature & Ch 1/2 Documentation
            if self.include_docs:
                if is_paper:
                    multi_tasks.append(
                        {
                            "task_id": "T1",
                            "description": "[Przyrost 1: Paper] Section I: Introduction, Motivation and Problem Statement in thesis.md",
                            "target_node": "v4",
                            "assigned_agent": writer_agent,
                            "status": "TODO",
                        }
                    )
                    multi_tasks.append(
                        {
                            "task_id": "T2",
                            "description": "[Przyrost 1: Paper] Section II: Related Work, SOTA Competitor Analysis and Research Gap in references.bib and thesis.md",
                            "target_node": "v4",
                            "assigned_agent": disc_agent,
                            "status": "TODO",
                        }
                    )
                elif t_type in ("magisterska", "master", "msc"):
                    multi_tasks.extend(
                        [
                            {
                                "task_id": "T1",
                                "description": "[Przyrost 1: Założenia] Redakcja Rozdziału 1: Wstęp, cel pracy i sformalizowana teza inżynierska w thesis.md",
                                "target_node": "v4",
                                "assigned_agent": writer_agent,
                                "status": "TODO",
                            },
                            {
                                "task_id": "T2_BG",
                                "description": "[Przyrost 1: Badania (II stopień)] Redakcja Rozdziału 2: Lejek teoretyczny od klasycznych monografii i podstaw w references.bib i thesis.md",
                                "target_node": "v4",
                                "assigned_agent": bg_agent,
                                "status": "TODO",
                            },
                            {
                                "task_id": "T2_DISC",
                                "description": "[Przyrost 1: Badania (II stopień)] Redakcja Rozdziału 2: Analiza najnowszego SOTA (2023-2026), konkurencji i luki badawczej w references.bib i thesis.md",
                                "target_node": "v4",
                                "assigned_agent": disc_agent,
                                "status": "TODO",
                            },
                        ]
                    )
                else:
                    multi_tasks.extend(
                        [
                            {
                                "task_id": "T1",
                                "description": "[Przyrost 1: Założenia] Redakcja Rozdziału 1: Wstęp, formalny cel pracy, definicja problemu i postawienie tezy inżynierskiej w thesis.md",
                                "target_node": "v4",
                                "assigned_agent": writer_agent,
                                "status": "TODO",
                            },
                            {
                                "task_id": "T2",
                                "description": "[Przyrost 1: Założenia] Redakcja Rozdziału 2: Stan badań, lejek literatury teoretycznej i analiza prac powiązanych w references.bib i thesis.md",
                                "target_node": "v4",
                                "assigned_agent": bg_agent,
                                "status": "TODO",
                            },
                        ]
                    )

            # Code & Tests for Slice 1: Domain Model & AST Interfaces
            t_idx = len(multi_tasks) + 1
            multi_tasks.append(
                {
                    "task_id": f"T{t_idx}",
                    "description": f"[Przyrost 1: Model i parametry] Zdefiniuj stałe i hiperparametry w config.py ({user_prompt[:70]}...)",
                    "target_node": "v1",
                    "assigned_agent": coder_agent,
                    "status": "TODO",
                }
            )
            t_idx += 1
            multi_tasks.append(
                {
                    "task_id": f"T{t_idx}",
                    "description": "[Przyrost 1: Model i parametry] Zbuduj testy jednostkowe walidacji parametrów i struktur w test_core.py",
                    "target_node": "v5",
                    "assigned_agent": tester_agent,
                    "status": "TODO",
                }
            )

            # Slice 2: Core Algorithm, Baseline & Architecture/Implementation Documentation
            t_idx += 1
            multi_tasks.append(
                {
                    "task_id": f"T{t_idx}",
                    "description": "[Przyrost 2: Algorytm i baseline] Zaimplementuj logikę algorytmu oraz metodę referencyjną w core.py",
                    "target_node": "v2",
                    "assigned_agent": coder_agent,
                    "status": "TODO",
                }
            )
            t_idx += 1
            multi_tasks.append(
                {
                    "task_id": f"T{t_idx}",
                    "description": "[Przyrost 2: Algorytm i baseline] Zbuduj testy jednostkowe poprawności algorytmu i metody bazowej w test_core.py",
                    "target_node": "v5",
                    "assigned_agent": tester_agent,
                    "status": "TODO",
                }
            )
            if self.include_docs:
                t_idx += 1
                multi_tasks.append(
                    {
                        "task_id": f"T{t_idx}",
                        "description": (
                            "[Przyrost 2: Architektura] Section III: System Architecture, Block Schematics and Formal Formulation in thesis.md"
                            if is_paper
                            else "[Przyrost 2: Architektura] Redakcja Rozdziału 3: Architektura systemu, schemat blokowy TikZ/Mermaid oraz formalizacja matematyczna modelu w thesis.md"
                        ),
                        "target_node": "v4",
                        "assigned_agent": writer_agent,
                        "status": "TODO",
                    }
                )
                t_idx += 1
                multi_tasks.append(
                    {
                        "task_id": f"T{t_idx}",
                        "description": (
                            "[Przyrost 2: Implementacja] Section IV: Algorithmic Implementation, AST Structures and Core Procedures in thesis.md"
                            if is_paper
                            else "[Przyrost 2: Implementacja] Redakcja Rozdziału 4: Implementacja algorytmiczna, struktury danych i dowiązania symboliczne do kodu AST w thesis.md"
                        ),
                        "target_node": "v4",
                        "assigned_agent": writer_agent,
                        "status": "TODO",
                    }
                )

            # Slice 3: Empirical Benchmark & Metrics + Quality Tests + Documentation (Ch 5 & 6)
            t_idx += 1
            multi_tasks.append(
                {
                    "task_id": f"T{t_idx}",
                    "description": "[Przyrost 3: Ewaluacja empiryczna] Przeprowadź badania porównawcze, zapisz results.csv i wygeneruj wykresy w plot_results.py",
                    "target_node": "v3",
                    "assigned_agent": tester_agent,
                    "status": "TODO",
                }
            )
            t_idx += 1
            multi_tasks.append(
                {
                    "task_id": f"T{t_idx}",
                    "description": "[Przyrost 3: Ewaluacja empiryczna] Zaimplementuj testy asercji jakościowych wyników i zbieżności w test_core.py",
                    "target_node": "v5",
                    "assigned_agent": tester_agent,
                    "status": "TODO",
                }
            )
            if self.include_docs:
                t_idx += 1
                multi_tasks.append(
                    {
                        "task_id": f"T{t_idx}",
                        "description": (
                            "[Przyrost 3: Wyniki] Section V: Empirical Results, Baseline Comparison and Sensitivity Analysis in thesis.md"
                            if is_paper
                            else "[Przyrost 3: Wyniki] Redakcja Rozdziału 5: Badania eksperymentalne, protokół pomiarowy, analiza wyników z tabelami CSV i wykresami w thesis.md"
                        ),
                        "target_node": "v4",
                        "assigned_agent": writer_agent,
                        "status": "TODO",
                    }
                )
                t_idx += 1
                multi_tasks.append(
                    {
                        "task_id": f"T{t_idx}",
                        "description": (
                            "[Przyrost 3: Podsumowanie] Section VI: Conclusion, Threats to Validity and Future Work in thesis.md"
                            if is_paper
                            else "[Przyrost 3: Podsumowanie] Redakcja Rozdziału 6: Podsumowanie, formalna weryfikacja tezy i wnioski końcowe w thesis.md"
                        ),
                        "target_node": "v4",
                        "assigned_agent": writer_agent,
                        "status": "TODO",
                    }
                )

            return multi_tasks

        if multi_cycle_waves and self.include_docs and cleaned and not is_paper and not needs_full_multi_cycle:
            missing_ch = [i for i in range(1, 7) if i not in covered_chapters]
            ch_descriptions = {
                1: "[Przyrost 1: Założenia] Redakcja Rozdziału 1: Wstęp, formalny cel pracy i teza inżynierska w thesis.md",
                2: "[Przyrost 1: Założenia] Redakcja Rozdziału 2: Przegląd literatury dziedzinowej i analiza SOTA w thesis.md",
                3: "[Przyrost 2: Architektura] Redakcja Rozdziału 3: Architektura systemu, schemat TikZ i model w thesis.md",
                4: "[Przyrost 2: Implementacja] Redakcja Rozdziału 4: Implementacja algorytmiczna i struktury AST w thesis.md",
                5: "[Przyrost 3: Eksperymenty] Redakcja Rozdziału 5: Badania eksperymentalne, protokół pomiarowy i dyskusja wyników w thesis.md",
                6: "[Przyrost 3: Podsumowanie] Redakcja Rozdziału 6: Podsumowanie, formalna weryfikacja tezy i wnioski w thesis.md",
            }
            for m_idx in missing_ch:
                custom_title = custom_ch_titles.get(m_idx)
                desc = (
                    f"Redakcja Rozdziału {m_idx} ({custom_title}) w thesis.md"
                    if custom_title
                    else ch_descriptions.get(m_idx, f"Redakcja Rozdziału {m_idx} w thesis.md")
                )
                ch_task = {
                    "task_id": f"T_CH{m_idx}",
                    "description": desc,
                    "target_node": "v4",
                    "assigned_agent": bg_agent if m_idx == 2 and t_type in ("inzynierska", "licencjacka") else writer_agent,
                    "status": "TODO",
                }
                if m_idx in (1, 2):
                    # Insert in Slice 1 before v2/v3 tasks
                    ins_idx = next(
                        (i for i, t in enumerate(cleaned) if t.get("target_node") in ("v2", "v3")),
                        len(cleaned),
                    )
                    cleaned.insert(ins_idx, ch_task)
                elif m_idx in (3, 4):
                    # Insert in Slice 2 before v3 tasks
                    ins_idx = next(
                        (i for i, t in enumerate(cleaned) if t.get("target_node") == "v3"),
                        len(cleaned),
                    )
                    cleaned.insert(ins_idx, ch_task)
                else:
                    # Append in Slice 3 at the end (after v3)
                    cleaned.append(ch_task)



        # Ensure every blast-radius affected node is covered if cleaned is missing required nodes
        covered_nodes = {t["target_node"] for t in cleaned}
        affected = [target for target in blast.get("affected_nodes", []) if target in ("v1", "v2", "v3", "v4")]
        node_default_desc = {
            "v1": "Zdefiniowanie hiperparametrów i stałych konfiguracyjnych w module config.py",
            "v2": "Implementacja głównego algorytmu oraz metody bazowej (baseline) w module core.py",
            "v3": "Ewaluacja empiryczna, wygenerowanie macierzy results.csv oraz wykresów w plot_results.py",
            "v4": "Opracowanie sekcji i rozdziałów pracy dyplomowej ze wskaźnikami symbolicznymi w thesis.md",
            "v5": "Implementacja testów jednostkowych pytest w module test_core.py",
        }
        healed_any = False
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
                        "description": node_default_desc.get(
                            req_node,
                            f"Aktualizacja węzła {req_node} wymuszona promieniem rażenia hipergrafu",
                        ),
                        "target_node": req_node,
                        "assigned_agent": ag,
                        "status": "TODO",
                    }
                )
                covered_nodes.add(req_node)
                healed_any = True

        if healed_any and multi_cycle_waves:
            research_agents = {"background_researcher", "discoverer_researcher", "sota_researcher"}
            has_research = any(t.get("assigned_agent") in research_agents for t in cleaned)
            if self.include_docs and not has_research:
                t_type = (thesis_type or "inzynierska").strip().lower()
                res_ag = disc_agent if t_type in ("paper", "article", "scientific_paper") else bg_agent
                cleaned.insert(
                    0,
                    {
                        "task_id": "T0_RES",
                        "description": "Przegląd literatury dziedzinowej i przygotowanie bibliografii w references.bib",
                        "target_node": "v4",
                        "assigned_agent": res_ag,
                        "status": "TODO",
                    },
                )
            node_order = {"v1": 1, "v2": 2, "v5": 3, "v3": 4, "v4": 5}
            cleaned.sort(
                key=lambda t: (
                    0
                    if t.get("assigned_agent") in research_agents
                    else node_order.get(str(t.get("target_node", "v1")), 3)
                )
            )
            for idx_t, t_item in enumerate(cleaned, 1):
                t_item["task_id"] = f"T{idx_t}"

        # Topological sanity check: ensure module implementation (v1, v2) precedes unit tests (v5)
        first_v2_idx = next((i for i, t in enumerate(cleaned) if t.get("target_node") == "v2"), None)
        if first_v2_idx is not None:
            early_v5_indices = [i for i, t in enumerate(cleaned[:first_v2_idx]) if t.get("target_node") == "v5"]
            if early_v5_indices:
                early_v5_tasks = [cleaned[i] for i in early_v5_indices]
                cleaned = [t for i, t in enumerate(cleaned) if i not in early_v5_indices]
                new_v2_idx = next(i for i, t in enumerate(cleaned) if t.get("target_node") == "v2")
                for offset, v5_t in enumerate(early_v5_tasks, 1):
                    cleaned.insert(new_v2_idx + offset, v5_t)

        return cleaned

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
            symbolic_errors = [str(err) for err in compiled.get("errors", [])][:12]

        csv_columns: list[str] = []
        csv_path = self.workspace_dir / "results.csv"
        if csv_path.exists():
            header = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
            csv_columns = [part.strip() for part in header[0].split(",")] if header else []

        trigger_issues = report.get("issues") or []
        if not isinstance(trigger_issues, list):
            trigger_issues = [trigger_issues]
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

    def _refresh_experiment_after_code(self, node_id: str) -> None:
        """After a code or test task, results.csv is whatever the experiment pipeline just wrote."""
        if str(self.provider).strip().lower() == "mock" or node_id not in {"v2", "v3"}:
            return
        from adk.tools.building.experiment_runner import execute_workspace_experiment

        result = execute_workspace_experiment(self.workspace_dir)
        if result.get("skipped") or result.get("ok"):
            self._last_experiment_error = ""
            return
        self._last_experiment_error = str(result.get("error") or "Eksperyment nie wygenerował results.csv")

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

    def _tasks_from_audit(self, audit: dict[str, Any], generation: int) -> list[dict[str, Any]]:
        """Turn the factual audit into the only tasks still worth doing."""
        prefix = f"Q{generation}"
        tasks: list[dict[str, Any]] = []
        if audit.get("pytest_status") != "PASS" or audit.get("pytest_errors"):
            py_errs = audit.get("pytest_errors") or []
            detail = "; ".join(py_errs) or "pytest nie przechodzi"
            test_fault = any("test_" in err.lower() or "_test.py" in err.lower() for err in py_errs)
            code_fault = any("core.py" in err.lower() or "syntax" in err.lower() or "assertionerror" in err.lower() for err in py_errs)
            plot_fault = any("plot" in err.lower() for err in py_errs)
            config_fault = any("config.py" in err.lower() for err in py_errs)

            if test_fault and not code_fault:
                tasks.append(
                    {
                        "task_id": f"{prefix}_TEST_FIX",
                        "description": f"Napraw testy w test_core.py, aby przechodziły czysto i nie naruszały reguł lintera. Błędy: {detail}",
                        "target_node": "v5",
                        "assigned_agent": "seed_tester",
                        "status": "TODO",
                    }
                )
            elif plot_fault and not code_fault:
                tasks.append(
                    {
                        "task_id": f"{prefix}_PLOT_FIX",
                        "description": f"Napraw skrypt wykresów plot_results.py. Błędy: {detail}",
                        "target_node": "v3",
                        "assigned_agent": "seed_tester",
                        "status": "TODO",
                    }
                )
            elif config_fault and not code_fault:
                tasks.append(
                    {
                        "task_id": f"{prefix}_CONFIG_FIX",
                        "description": f"Napraw stałe i parametry w config.py. Błędy: {detail}",
                        "target_node": "v1",
                        "assigned_agent": "seed_coder",
                        "status": "TODO",
                    }
                )
            else:
                tasks.append(
                    {
                        "task_id": f"{prefix}_CODE",
                        "description": f"Napraw kod tak, żeby pytest przeszedł. Stan faktyczny: {detail}",
                        "target_node": "v2",
                        "assigned_agent": "seed_coder",
                        "status": "TODO",
                    }
                )
                if test_fault or not (self.workspace_dir / "test_core.py").exists():
                    tasks.append(
                        {
                            "task_id": f"{prefix}_TESTS",
                            "description": f"Zsynchronizuj testy w test_core.py z kodem i usuń błędy asercji/importów. Błędy: {detail}",
                            "target_node": "v5",
                            "assigned_agent": "seed_tester",
                            "status": "TODO",
                        }
                    )
                else:
                    tasks.append(
                        {
                            "task_id": f"{prefix}_TESTS",
                            "description": "Uruchom train_and_evaluate i zapisz results.csv zgodny z tym, co funkcja zwraca. Testy mają wołać kod, a nie sprawdzać wklejone liczby.",
                            "target_node": "v3",
                            "assigned_agent": "seed_tester",
                            "status": "TODO",
                        }
                    )
        elif not audit.get("csv_columns"):
            tasks.append(
                {
                    "task_id": f"{prefix}_CSV",
                    "description": "Wygeneruj results.csv przez train_and_evaluate. Pliku wynikowego nie ma.",
                    "target_node": "v3",
                    "assigned_agent": "seed_tester",
                    "status": "TODO",
                }
            )
        for number in audit.get("chapters_missing") or []:
            tasks.append(
                {
                    "task_id": f"{prefix}_CH{number}",
                    "description": f"Napisz Rozdział {number} w thesis.md. Zastąp sekcję, nie doklejaj drugiej kopii.",
                    "target_node": "v4",
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        trigger_text = " ".join(str(item) for item in (audit.get("trigger_issues") or [])).lower()
        if any(token in trigger_text for token in ("pdf", "tectonic", "latex")):
            tasks.append(
                {
                    "task_id": f"{prefix}_PDF",
                    "description": (
                        "Kompilacja thesis.pdf nie przeszła. Popraw thesis.md i kod tak, "
                        f"żeby LaTeX się zbudował. Log: {trigger_text[:1500]}"
                    ),
                    "target_node": "v4",
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        if audit.get("symbolic_errors"):
            detail = "; ".join(audit["symbolic_errors"])
            tasks.append(
                {
                    "task_id": f"{prefix}_REFS",
                    "description": f"Popraw thesis.md tak, aby zostały tylko wskaźniki istniejące w plikach. Błędy: {detail}",
                    "target_node": "v4",
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        if not tasks:
            detail = "; ".join(audit.get("trigger_issues") or []) or "bramka końcowa nie przeszła"
            tasks.append(
                {
                    "task_id": f"{prefix}_CLOSE",
                    "description": f"Domykanie pracy na podstawie audytu. Do usunięcia: {detail}",
                    "target_node": "v4",
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        return tasks

    def _shout_problem_stop(self, reason: str) -> None:
        """Console and process log. A stop because of a problem must be impossible to miss."""
        banner = "\n".join(
            [
                "",
                "PPPP   RRRR   ZZZZZ  EEEEE  RRRR   Y   Y  W   W   AAA   M   M",
                "P   P  R   R     Z   E      R   R   Y Y   W   W  A   A  MM MM",
                "PPPP   RRRR     Z    EEEE   RRRR     Y    W W W  AAAAA  M M M",
                "P      R  R    Z     E      R  R     Y    WW WW  A   A  M   M",
                "P      R   R  ZZZZZ  EEEEE  R   R    Y    W   W  A   A  M   M",
                "",
                "BBBB    OOO        JJJ  EEEEE  SSSSS  TTTTT",
                "B   B  O   O         J  E      S        T",
                "BBBB   O   O         J  EEEE   SSSSS    T",
                "B   B  O   O     J   J  E          S    T",
                "BBBB    OOO       JJJ   EEEEE  SSSSS    T",
                "",
                "PPPP   RRRR    OOO   BBBBB  L      EEEEE  M   M",
                "P   P  R   R  O   O  B   B  L      E      MM MM",
                "PPPP   RRRR   O   O  BBBBB  L      EEEE   M M M",
                "P      R  R   O   O  B   B  L      E      M   M",
                "P      R   R   OOO   BBBBB  LLLLL  EEEEE  M   M",
                "",
                reason,
                "",
            ]
        )
        print(banner, flush=True)
        self.logger.log_step("PRZERWANIE", banner, {"reason": reason})

    def _rebuild_queue(self, report: dict[str, Any], generation: int, last_signature: str | None) -> dict[str, Any]:
        """After 3 failed repairs, drop the old queue and return a new one, or a terminal payload."""
        audit = self._audit_factual_state(report)
        signature = _issue_signature(
            {
                "issues": audit.get("pytest_errors", [])
                + [f"missing-chapter-{n}" for n in audit.get("chapters_missing", [])]
                + audit.get("symbolic_errors", [])
                + audit.get("trigger_issues", [])
            }
        )
        print(
            f"\n  [AUDYT STANU] pytest={audit.get('pytest_status')}, "
            f"brak rozdziałów={audit.get('chapters_missing')}, "
            f"błędy symboliczne={len(audit.get('symbolic_errors') or [])}",
            flush=True,
        )
        if (signature == last_signature and generation >= 2) or generation >= 4:
            if signature == last_signature:
                reason = "AUDYT PLIKOW SIE NIE ZMIENIL PO WIELOKROTNYCH PROBACH. STAN PRACY NADAL JEST ZLY."
            else:
                reason = "WYCZERPANO CZTERY PRZEBUDOWY KOLEJKI. STAN PRACY NADAL JEST ZLY."
            self._shout_problem_stop(reason)
            self._update_hitl_gate(
                gate_name="GATE_QUEUE_REBUILD_EXHAUSTED",
                active=True,
                question="Przebudowy kolejki nie zmieniły stanu plików albo limit przebudów został wyczerpany.",
                context={"audit": audit, "generation": generation},
            )
            return {
                "stop": {
                    "status": "HITL_PAUSED",
                    "reason": "QUEUE_REBUILD_EXHAUSTED",
                    "gate": "GATE_QUEUE_REBUILD_EXHAUSTED",
                    "hitl": read_json_state(self.hitl_flag_path),
                    "audit": audit,
                }
            }
        tasks = self._tasks_from_audit(audit, generation + 1)
        write_json_state(self.task_queue_path, tasks)
        print(
            f"  [NOWA KOLEJKA {generation + 1}/3] {len(tasks)} zadań z audytu, stara kolejka przerwana.",
            flush=True,
        )
        self._record_evolution_event(
            {"type": "QUEUE_REBUILT", "generation": generation + 1, "task_ids": [t["task_id"] for t in tasks]}
        )
        return {"tasks": tasks, "signature": signature}

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
        """Execute the full Neuro-Symbolic Harness pipeline."""
        self.current_user_prompt = user_prompt
        self.multi_cycle_waves = multi_cycle_waves
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

        # 1. Planning (Layer 1): Domain Reconnaissance + TOC Synthesis + Task Decomposition
        print(
            f"\n[WARSTWA 1: PLANOWANIE] Obliczanie promienia razenia hipergrafu od wezla '{target_node}' -> wezly: {blast.get('affected_nodes', [])}",
            flush=True,
        )

        tpl_detection = detect_template_from_prompt(
            user_prompt,
            thesis_type=thesis_type,
            requested_template=template_name,
        )
        detected_thesis_type = str(tpl_detection.get("thesis_type") or "inzynierska")
        detected_template = str(tpl_detection.get("template_name") or "thesis_plodz")
        template_is_certain = bool(tpl_detection.get("is_certain", False))

        initial_recon = scout_domain_conventions(user_prompt, thesis_type=detected_thesis_type)
        suggested_sections = [
            str(p).split(":")[0].strip() if ":" in str(p) else str(p).strip()
            for p in initial_recon.get("common_structural_patterns", [])
        ]
        domain_summary = {
            "domain": initial_recon.get("domain"),
            "topic_canonical": initial_recon.get("topic_canonical"),
            "canonical_baselines": initial_recon.get("canonical_baselines", []),
            "standard_metrics": initial_recon.get("standard_metrics", []),
            "open_research_gaps": initial_recon.get("open_research_gaps", []),
            "suggested_sections": suggested_sections,
            "detected_thesis_type": detected_thesis_type,
            "detected_template_name": detected_template,
            "template_is_certain": template_is_certain,
        }

        # Natychmiast zapisujemy bazowy academic_blueprint na dysk dla Layer 2 workers
        base_blueprint = {
            "thesis_type": detected_thesis_type,
            "template_name": detected_template,
            "template_certain": template_is_certain,
            "thesis_title": initial_recon.get("topic_canonical", user_prompt),
            "literature_recon": initial_recon,
        }
        write_json_state(self.blueprint_path, base_blueprint)

        plan_payload: dict[str, Any] = {
            "user_prompt": user_prompt,
            "target_node": target_node,
            "blast_radius": blast,
            "hypergraph": scoped_graph,
            "hypergraph_matrix": scoped_graph,
            "agent_registry": read_json_state(self.registry_path),
            "include_docs": self.include_docs,
            "missing_agent_specialization": missing_agent_specialization,
            "domain_context": domain_summary,
            "detected_template": tpl_detection,
        }
        planner_md = self.agents_dir / "planning" / "task_planner.md"

        plan_out = call_agent(
            planner_md,
            plan_payload,
            model_tier="LRM",
            provider=self.provider,
        )["output"]

        # Stopień 1: Refleksyjna ewolucja promptu planisty w przypadku pustej listy zadań
        raw_tasks_candidate = plan_out.get("tasks")
        if not raw_tasks_candidate or not isinstance(raw_tasks_candidate, list) or len(raw_tasks_candidate) == 0:
            self.logger.log_step(
                "PLANNER_REFLEXIVE_EVOLUTION",
                "task_planner zwrócił 0 zadań. Wykonuję refleksyjną ewolucję promptu z informacją zwrotną o błędzie.",
                {"first_attempt": plan_out},
            )
            healing_payload = dict(plan_payload)
            healing_payload["reflection_feedback"] = (
                "BŁĄD: Poprzednia odpowiedź nie zawierała listy zadań w polu 'tasks'. "
                "Wymagane jest umieszczenie tablicy 'tasks' jako pierwszego klucza w JSON z co najmniej 3 przyrostami "
                "(Vertical Feature Slices): kod, testy jednostkowe i opis w pracy dyplomowej."
            )
            retry_res = call_agent(
                planner_md,
                healing_payload,
                model_tier="LRM",
                provider=self.provider,
            )
            if retry_res.get("status") == "ok":
                cand = retry_res.get("output", {})
                if cand.get("tasks") and isinstance(cand.get("tasks"), list) and len(cand.get("tasks")) > 0:
                    plan_out = cand

        # Stopień 2: Ewolucja Warstwy 4 (Prompt Mutation) w przypadku powtórnego braku zadań
        if (not plan_out.get("tasks") or len(plan_out.get("tasks")) == 0) and self.enable_layer4:
            self.logger.log_step(
                "PLANNER_LAYER4_MUTATION",
                "task_planner nie zdołał wygenerować zadań. Wywołuję Architekta Ewolucji (W4) do mutacji promptu...",
            )
            evo_res = self._run_evolution_step({
                "failed_agent": "task_planner",
                "suggested_rule": "MUST ALWAYS place 'tasks' array with at least 3 vertical feature slices (code, test, doc) at the top of JSON.",
            })
            self._record_evolution_event({"type": "PLANNER_PROMPT_MUTATED", "details": evo_res})
            mutated_retry = call_agent(
                planner_md,
                plan_payload,
                model_tier="LRM",
                provider=self.provider,
            )
            if mutated_retry.get("status") == "ok":
                cand = mutated_retry.get("output", {})
                if cand.get("tasks") and isinstance(cand.get("tasks"), list) and len(cand.get("tasks")) > 0:
                    plan_out = cand

        planned_thesis_type = str(
            (detected_thesis_type if template_is_certain else None)
            or plan_out.get("thesis_type")
            or detected_thesis_type
        )
        self.planned_thesis_type = planned_thesis_type
        planned_template = resolve_template_name(
            thesis_type=planned_thesis_type,
            requested_template=(
                (detected_template if template_is_certain else None)
                or plan_out.get("template_name")
            ),
        )
        self.planned_template = planned_template
        if not template_is_certain and not plan_out.get("template_name"):
            tpl_question = str(tpl_detection.get("question") or "Którego szablonu użyć: 'thesis_plodz' czy 'paper_ieee'?")
            self.logger.log_step(
                "TEMPLATE_UNCERTAIN_HITL",
                f"Brak jednoznacznego określenia szablonu w zapytaniu -> zapytanie użytkownika: {tpl_question}",
                {"detected_template": tpl_detection},
            )
            if gate_approval_callback is None and self.gate_approval_callback is None:
                planned_template, planned_thesis_type = prompt_user_for_template(
                    default_template=planned_template,
                    default_thesis_type=planned_thesis_type,
                )

        recon_report = scout_domain_conventions(user_prompt, thesis_type=planned_thesis_type)
        blueprint_raw = dict(plan_out.get("academic_blueprint") or {})
        blueprint_raw["literature_recon"] = recon_report
        blueprint_raw["thesis_type"] = planned_thesis_type
        blueprint_raw["template_name"] = planned_template
        blueprint_raw["template_certain"] = bool(template_is_certain or plan_out.get("template_name"))

        # Dynamiczne rozdziały zaplanowane przez task_planner
        toc_candidate = blueprint_raw.get("table_of_contents") or plan_out.get("table_of_contents")
        if isinstance(toc_candidate, dict):
            toc_chapters_candidate = toc_candidate.get("chapters", [])
        elif isinstance(toc_candidate, list):
            toc_chapters_candidate = toc_candidate
        else:
            toc_chapters_candidate = None

        planned_chapters = (
            blueprint_raw.get("planned_chapters")
            or plan_out.get("planned_chapters")
            or toc_chapters_candidate
        )
        if not planned_chapters:
            toc_fallback = synthesize_table_of_contents(
                user_prompt,
                thesis_type=planned_thesis_type,
                recon_report=recon_report,
                title_pl=str(blueprint_raw.get("thesis_title") or ""),
            )
            planned_chapters = toc_fallback.get("chapters", [])

        toc_structure = {"chapters": planned_chapters} if isinstance(planned_chapters, list) else planned_chapters
        blueprint_raw["table_of_contents"] = toc_structure
        blueprint_raw["planned_chapters"] = planned_chapters
        plan_out["academic_blueprint"] = blueprint_raw
        write_json_state(self.blueprint_path, blueprint_raw)

        toc_structure = blueprint_raw.get("table_of_contents", {})
        toc_chapters = toc_structure.get("chapters", []) if isinstance(toc_structure, dict) else toc_structure
        self.logger.log_step(
            "PLANNING_RECON_TOC",
            f"Rekonesans literatury ({recon_report.get('domain')}) i synteza Spisu Tresci ({len(toc_chapters)} rozdzialow, typ={planned_thesis_type})",
            {
                "thesis_type": planned_thesis_type,
                "task_key": recon_report.get("task_key"),
                "canonical_baselines": recon_report.get("canonical_baselines", []),
                "standard_metrics": recon_report.get("standard_metrics", []),
                "chapters_count": len(toc_chapters),
            },
        )
        print(
            f"  [WARSTWA 1: REKONESANS LITERATURY I SPIS TRESCI] Dziedzina: '{recon_report.get('domain')}' | "
            f"Typ: {planned_thesis_type} | Rozdzialy w TOC: {len(toc_chapters)} | "
            f"Metryki: {', '.join(recon_report.get('standard_metrics', [])[:4])}",
            flush=True,
        )

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
                and t.get("assigned_agent") not in ("seed_writer", "sota_researcher", "background_researcher", "discoverer_researcher")
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
                thesis_type=planned_thesis_type,
                planned_chapters=planned_chapters if isinstance(planned_chapters, list) else None,
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
                thesis_type=planned_thesis_type,
                planned_chapters=planned_chapters if isinstance(planned_chapters, list) else None,
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

        # Only trigger simulated failures in mock testing mode, never in live LLM runs
        is_mock = str(self.provider).strip().lower() == "mock"
        if simulate_first_attempt_fail and is_mock and multi_cycle_waves:
            v1_idx = next((i for i, t in enumerate(tasks) if t.get("target_node") == "v1"), 0)
            v3_idx = next((i for i, t in enumerate(tasks) if t.get("target_node") == "v3"), min(2, len(tasks) - 1))
            v4_writer_idx = next(
                (i for i in range(len(tasks) - 1, -1, -1) if tasks[i].get("target_node") == "v4"),
                len(tasks) - 1,
            )
            wave_fail_indices = {v1_idx, v3_idx, v4_writer_idx}
        elif simulate_first_attempt_fail and is_mock:
            wave_fail_indices = {0}
        else:
            wave_fail_indices = set()

        execution_generation = 0
        last_audit_signature: str | None = None
        while True:
            exhausted_report: dict[str, Any] | None = None
            for idx, task in enumerate(tasks):
                task["status"] = "IN_PROGRESS"
                write_json_state(self.task_queue_path, tasks)

                raw_node_id = str(task.get("target_node", "v1"))
                node_id, node_file = self._resolve_target_node(raw_node_id, task=task, fallback="v1")
                task["target_node"] = node_id
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

                builder_error_msg: str | None = None
                try:
                    self._execute_builder_step(task, model_tier=tier)
                    self._refresh_experiment_after_code(node_id)
                except Exception as exc:
                    builder_error_msg = f"Wyjątek wykonania zadania {t_id} na węźle {node_id} ({node_file}): {exc}"
                    print(
                        f"  [OSTRZEŻENIE: BŁĄD BUDOWANIA] {builder_error_msg}",
                        flush=True,
                    )

                should_fail = execution_generation == 0 and idx in wave_fail_indices
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
                if builder_error_msg:
                    report["status"] = "FAIL"
                    report.setdefault("issues", []).append(builder_error_msg)
                    report.setdefault("errors", []).append(builder_error_msg)

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

                    issues_list = report.get("issues", [])
                    issues_summary = "; ".join(issues_list) if issues_list else "Usterka weryfikacji warstwy 3"
                    remediation_directive = (
                        f"Poprzednio nie zadziałało: {issues_summary}. "
                        f"Zrób to: w zadaniu {t_id} na węźle {node_id} ({node_file}) wyeliminuj ten błąd i wygeneruj w pełni poprawną zawartość."
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
                                "suggested_rule": remediation_directive,
                            },
                            tasks_in_memory=tasks,
                        )
                        cycle_trace["w4_action"] = str(evo_res.get("action") or evo_res.get("decision") or "MUTATE_AGENT")
                        print(
                            f"  [WARSTWA 4 -> DECYZJA] Wykonano akcje ewolucyjna: {cycle_trace['w4_action']}",
                            flush=True,
                        )
                        if evo_res.get("action") == "HITL" or evo_res.get("decision") == "HITL":
                            if not self.interactive_gates and self.gate_approval_callback is None:
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
                            else:
                                return {
                                    "status": "HITL_PAUSED",
                                    "layer4": evo_res,
                                    "tasks": tasks,
                                    "replan_count": replan_count,
                                    "architecture_cycles": architecture_cycles,
                                }

                    remediation_agent = self.agents_dir / "planning" / "remediation_planner.md"

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
                            "remediation_directive": remediation_directive,
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

                    # Update remaining TODO tasks (and append any newly spawned tasks) if remediation_planner emitted updated_pending_tasks
                    updated_pending = remediation_out.get("updated_pending_tasks")
                    if isinstance(updated_pending, list) and updated_pending:
                        existing_ids = {str(t.get("task_id", "")) for t in tasks if isinstance(t, dict)}
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
                        for ut in updated_pending:
                            if not isinstance(ut, dict):
                                continue
                            ut_id = str(ut.get("task_id") or f"T{len(tasks) + 1}_DYN")
                            if ut_id not in existing_ids and ut.get("description"):
                                ut_node = str(ut.get("target_node") or node_id)
                                if ut_node not in ("v1", "v2", "v3", "v4", "v5"):
                                    ut_node = node_id
                                ut_ag = self._resolve_active_agent(
                                    str(ut.get("assigned_agent") or "seed_coder"),
                                    fallback="seed_writer" if ut_node == "v4" else "seed_coder",
                                )
                                tasks.append(
                                    {
                                        "task_id": ut_id,
                                        "description": str(ut.get("description")),
                                        "target_node": ut_node,
                                        "assigned_agent": ut_ag,
                                        "status": "TODO",
                                    }
                                )
                                existing_ids.add(ut_id)

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
                        surgical_tasks = [
                            {
                                "task_id": f"{task.get('task_id', 'T1')}_FIX",
                                "target_node": node_id,
                                "assigned_agent": failed_agent,
                                "description": f"Poprzednio nie zadziałało: {issues_summary}. Zrób to: napraw węzeł {node_id} ({node_file}) i wyeliminuj błędy.",
                                "status": "TODO",
                            }
                        ]

                    remediation_errors: list[str] = []
                    for stask in surgical_tasks:
                        if not isinstance(stask, dict):
                            continue
                        st_raw_node = stask.get("target_node") or node_id
                        st_node, st_file = self._resolve_target_node(st_raw_node, task=stask, fallback=node_id)
                        stask["target_node"] = st_node
                        node_default_agent = {
                            "v1": "seed_coder",
                            "v2": "seed_coder",
                            "v3": "seed_tester",
                            "v4": "seed_writer",
                            "v5": "seed_tester",
                        }.get(st_node, "seed_coder")
                        raw_assigned = str(stask.get("assigned_agent") or "").strip()
                        if not raw_assigned or (st_node in ("v1", "v2", "v3", "v5") and "writer" in raw_assigned):
                            target_ag = node_default_agent
                        else:
                            target_ag = raw_assigned
                        stask["assigned_agent"] = self._resolve_active_agent(
                            target_ag,
                            fallback=node_default_agent,
                        )
                        stask.setdefault("task_id", f"{task.get('task_id', 'T1')}_FIX")
                        orig_desc = str(task.get("description", "")).strip()
                        st_desc = str(stask.get("description", "")).strip()
                        if stask.get("target_node") == "v4" and orig_desc and orig_desc[:30].lower() not in st_desc.lower():
                            stask["description"] = f"[Kontekst sekcji: {orig_desc}] {st_desc}"
                        cycle_trace["w1_remediation_task_id"] = str(stask["task_id"])
                        st_tier = select_model_tier(st_node, self.matrix_path)
                        print(
                            f"  [WARSTWA 2: BUDOWANIE NAPRAWCZE] Zadanie chirurgiczne {stask['task_id']} "
                            f"[{st_file}] przez agenta '{stask['assigned_agent']}' (Tier: {st_tier})...",
                            flush=True,
                        )
                        try:
                            self._execute_builder_step(stask, model_tier=st_tier)
                        except Exception as exc:
                            err_msg = f"Wyjątek zadania naprawczego {stask.get('task_id')} na węźle {st_node} ({st_file}): {exc}"
                            print(
                                f"  [OSTRZEŻENIE: BŁĄD ZADANIA NAPRAWCZEGO] {err_msg}",
                                flush=True,
                            )
                            remediation_errors.append(err_msg)

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
                    if remediation_errors:
                        report["status"] = "FAIL"
                        report.setdefault("issues", []).extend(remediation_errors)
                        report.setdefault("errors", []).extend(remediation_errors)
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
                    task["status"] = "FAILED"
                    write_json_state(self.task_queue_path, tasks)
                    # Check if there are companion tasks in this queue targeting other nodes
                    remaining_other_nodes = [
                        t for t in tasks[idx + 1 :]
                        if isinstance(t, dict) and t.get("status") == "TODO" and t.get("target_node") != node_id
                    ]
                    if remaining_other_nodes:
                        print(
                            f"  [KONTYNUACJA KOLEJKI] Zadanie {t_id} ma status FAILED, ale w kolejce są powiązane zadania "
                            f"na innych węzłach ({[t.get('target_node') for t in remaining_other_nodes]}). Kontynuuję kolejkę przed audytem stanu.",
                            flush=True,
                        )
                        continue
                    else:
                        print(
                            f"  [KOLEJKA PRZERWANA] Zadanie {t_id} nie zostało naprawione w {task_retries} próbach. "
                            "Audyt stanu i nowa kolejka.",
                            flush=True,
                        )
                        exhausted_report = report
                        break

            # If any tasks were marked FAILED and we didn't break early, check workspace health
            if exhausted_report is None:
                failed_any = [t for t in tasks if isinstance(t, dict) and t.get("status") == "FAILED"]
                if failed_any:
                    final_chk = self._run_verification_step(
                        tasks[-1] if tasks else {"target_node": "v2", "task_id": "QUEUE_FINAL"},
                        include_docs=self.include_docs,
                        is_final_gate=False,
                        inject_failure=False,
                    )
                    if final_chk.get("status") != "PASS":
                        exhausted_report = final_chk

            if exhausted_report is not None:
                rebuilt = self._rebuild_queue(exhausted_report, execution_generation, last_audit_signature)
                if 'stop' in rebuilt:
                    stop = rebuilt['stop']
                    stop['tasks'] = tasks
                    stop['replan_count'] = replan_count
                    stop['architecture_cycles'] = architecture_cycles
                    stop['validation_report'] = exhausted_report
                    return stop
                tasks = rebuilt['tasks']
                last_audit_signature = rebuilt['signature']
                execution_generation += 1
                continue

            # 4. Final Defense Verification & Gate 3 Promotor Checkpoint (W3 -> W1 -> W2 -> W3 Remediation Loop)
            defense_target_task = tasks[-1] if tasks else {"target_node": "v4", "task_id": "FINAL_DEFENSE"}
            print(
                "\n  [WARSTWA 3: BRAMKA KONCOWA OBRONY PRACY (GATE_3_DEFENSE_APPROVAL)] Pelna walidacja kodu, CSV i 6 rozdzialow pracy...",
                flush=True,
            )
            final_report = self._run_verification_step(
                defense_target_task,
                include_docs=self.include_docs,
                is_final_gate=True,
                inject_failure=False,
            )

            defense_retries = 0
            while final_report.get("status") != "PASS" and defense_retries < effective_max_retries:
                defense_retries += 1
                replan_count += 1
                defense_issues = "; ".join(final_report.get("issues", [])) or "Usterka obrony pracy (Gate 3)"
                print(
                    f"\n  [WARSTWA 3 -> ODRZUCENIE OBRONY GATE 3] Proba naprawy #{defense_retries}: {defense_issues}\n"
                    f"  [POWROT DO WARSTWY 1: REMEDIACJA OBRONY] Synteza zadan naprawczych dla Gate 3...",
                    flush=True,
                )
                def_node = str(final_report.get("failed_file") or "v4")
                if not def_node.startswith("v"):
                    def_node = next(
                        (nid for nid, nmeta in matrix_nodes.items() if nmeta.get("path") == def_node),
                        "v4",
                    )
                remediation_agent = self.agents_dir / "planning" / "remediation_planner.md"
                def_remed_out = call_agent(
                    remediation_agent,
                    {
                        "user_prompt": user_prompt,
                        "error_report": final_report,
                        "failed_task": {
                            "task_id": f"GATE_3_FIX_{defense_retries}",
                            "target_node": def_node,
                            "assigned_agent": "seed_writer" if def_node == "v4" else "seed_coder",
                        },
                        "remediation_directive": f"Poprzednio nie zadziałało podczas obrony Gate 3: {defense_issues}. Zrób to: usun usterki i doprowadz prace do pelnej zgodnosci.",
                        "failure_ledger": read_json_state(self.failure_ledger_path) if self.failure_ledger_path.exists() else {"failures": []},
                        "agent_registry": read_json_state(self.registry_path),
                        "blast_radius": calculate_blast_radius(def_node, self.matrix_path),
                        "hypergraph": get_scoped_hypergraph_context(self.matrix_path, blast_radius=calculate_blast_radius(def_node, self.matrix_path)),
                        "hypergraph_matrix": get_scoped_hypergraph_context(self.matrix_path, blast_radius=calculate_blast_radius(def_node, self.matrix_path)),
                        "include_docs": self.include_docs,
                    },
                    model_tier="LRM",
                    provider=self.provider,
                )["output"]

                def_tasks = def_remed_out.get("surgical_tasks") or def_remed_out.get("tasks") or []
                if not isinstance(def_tasks, list):
                    def_tasks = []

                # If missing chapters were reported, ensure surgical tasks cover each missing chapter explicitly
                missing_ch_match = re.search(r"brakujące rozdziały.*?\[(.*?)\]", defense_issues)
                if missing_ch_match:
                    raw_missing = missing_ch_match.group(1).lower()
                    for ch_i in range(1, 7):
                        if f"rozdział {ch_i}" in raw_missing or f"rozdzia\u0142 {ch_i}" in raw_missing:
                            ch_desc_map = {
                                1: "Zredaguj Rozdział 1: Wstęp, cel pracy i sformalizowaną tezę inżynierską w thesis.md",
                                2: "Zredaguj Rozdział 2: Stan wiedzy, lejek literatury teoretycznej i analizę SOTA w references.bib i thesis.md",
                                3: "Zredaguj Rozdział 3: Architektura systemu, schemat TikZ i formalizm matematyczny w thesis.md",
                                4: "Zredaguj Rozdział 4: Implementacja algorytmiczna i struktury AST w thesis.md",
                                5: "Zredaguj Rozdział 5: Badania eksperymentalne, protokół pomiarowy i dyskusja wyników z results.csv w thesis.md",
                                6: "Zredaguj Rozdział 6: Podsumowanie, formalna weryfikacja tezy i wnioski końcowe w thesis.md",
                            }
                            if not any(f"rozdział {ch_i}" in str(t.get("description", "")).lower() for t in def_tasks if isinstance(t, dict)):
                                def_tasks.append({
                                    "task_id": f"GATE_3_CH{ch_i}_FIX",
                                    "target_node": "v4",
                                    "assigned_agent": "seed_writer",
                                    "description": ch_desc_map.get(ch_i, f"Zredaguj Rozdział {ch_i} w thesis.md"),
                                    "status": "TODO",
                                })

                if not def_tasks:
                    def_tasks = [
                        {
                            "task_id": f"GATE_3_FIX_{defense_retries}",
                            "target_node": def_node,
                            "assigned_agent": "seed_writer" if def_node == "v4" else "seed_coder",
                            "description": f"Poprzednio nie zadziałało: {defense_issues}. Zrób to: usun bledy obrony pracy.",
                            "status": "TODO",
                        }
                    ]

                for dtask in def_tasks:
                    if not isinstance(dtask, dict):
                        continue
                    raw_dt_node = str(dtask.get("target_node") or def_node)
                    dt_node, dt_file = self._resolve_target_node(raw_dt_node, task=dtask, fallback="v4")
                    dtask["target_node"] = dt_node
                    node_default_agent = {
                        "v1": "seed_coder",
                        "v2": "seed_coder",
                        "v3": "seed_tester",
                        "v4": "seed_writer",
                        "v5": "seed_tester",
                    }.get(dt_node, "seed_writer")
                    raw_assigned = str(dtask.get("assigned_agent") or "").strip()
                    if not raw_assigned or (dt_node in ("v1", "v2", "v3", "v5") and "writer" in raw_assigned):
                        target_ag = node_default_agent
                    else:
                        target_ag = raw_assigned
                    dtask["assigned_agent"] = self._resolve_active_agent(
                        target_ag,
                        fallback=node_default_agent,
                    )
                    dt_tier = select_model_tier(dt_node, self.matrix_path)
                    print(
                        f"  [WARSTWA 2: BUDOWANIE NAPRAWCZE DLA GATE 3] Zadanie {dtask.get('task_id')} "
                        f"[{dt_file}] na wezle {dt_node} przez agenta '{dtask['assigned_agent']}'...",
                        flush=True,
                    )
                    try:
                        self._execute_builder_step(dtask, model_tier=dt_tier)
                        self._refresh_experiment_after_code(dt_node)
                    except Exception as exc:
                        print(
                            f"  [OSTRZEŻENIE: BŁĄD OBRONY GATE 3] Wyjątek w zadaniu {dtask.get('task_id')}: {exc}",
                            flush=True,
                        )
                        defense_issues += f" | Błąd wykonania zadania obrony {dtask.get('task_id')}: {exc}"
                    dtask["status"] = "DONE"
                    if multi_cycle_waves:
                        tasks.append(dtask)
                        write_json_state(self.task_queue_path, tasks)

                print(
                    f"  [WARSTWA 3: RE-AUDYT GATE 3] Ponowna weryfikacja obrony po naprawie #{defense_retries}...",
                    flush=True,
                )
                final_report = self._run_verification_step(
                    defense_target_task,
                    include_docs=self.include_docs,
                    is_final_gate=True,
                    inject_failure=False,
                )

            defense_ok = final_report.get("status") == "PASS"
            if defense_ok:
                pdf_report = self._pdf_failure_report()
                if pdf_report is not None:
                    print(
                        "  [PDF] Kompilacja nie przeszła. Audyt stanu i nowa kolejka.",
                        flush=True,
                    )
                    rebuilt = self._rebuild_queue(pdf_report, execution_generation, last_audit_signature)
                    if "stop" in rebuilt:
                        stop = rebuilt["stop"]
                        stop["tasks"] = tasks
                        stop["replan_count"] = replan_count
                        stop["architecture_cycles"] = architecture_cycles
                        stop["validation_report"] = pdf_report
                        return stop
                    tasks = rebuilt["tasks"]
                    last_audit_signature = rebuilt["signature"]
                    execution_generation += 1
                    continue
            if not defense_ok:
                print(
                    f"  [KOLEJKA PRZERWANA] Obrona Gate 3 nie przeszła po {defense_retries} próbach. "
                    "Audyt stanu i nowa kolejka.",
                    flush=True,
                )
                exhausted_report = final_report
                rebuilt = self._rebuild_queue(exhausted_report, execution_generation, last_audit_signature)
                if "stop" in rebuilt:
                    stop = rebuilt["stop"]
                    stop["tasks"] = tasks
                    stop["replan_count"] = replan_count
                    stop["architecture_cycles"] = architecture_cycles
                    stop["validation_report"] = final_report
                    return stop
                tasks = rebuilt["tasks"]
                last_audit_signature = rebuilt["signature"]
                execution_generation += 1
                continue

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

            status_label = "COMPLETED"
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
