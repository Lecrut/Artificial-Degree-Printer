"""Layer 2: run a builder agent and write its output to the workspace."""

from __future__ import annotations


import os
import re
import time
from typing import Any

from adk.core.models import read_json_state
from adk.tools.building import (
    edit_ast_node,
    edit_document_section,
    extract_hyperedge_exports,
    sync_hypergraph_matrix,
)
from adk.tools.planning import (
    calculate_blast_radius,
    get_scoped_hypergraph_context,
)
from adk.orchestration.common import (
    _filter_bibtex,
    _merge_bibtex_entries,
    _is_document,
    MaterializationError,
    OUTPUT_SCHEMA,
    _METADATA_KEYS,
    build_grounded_symbols,
)


class BuildingMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _materialize_workspace_artifact(self, node_path: str, llm_output: dict[str, Any]) -> None:
        """Write a builder's output to the workspace. Accepted shapes are listed in OUTPUT_SCHEMA; an answer that
        carries content in none of them is an error returned to the agent, never a silent no-op."""
        full_file_path = self.workspace_dir / node_path
        materialized_any = False
        ws_root = self.workspace_dir.resolve()

        def _normalize_raw_code(raw_text: Any) -> str | None:
            if not isinstance(raw_text, str) or not raw_text.strip():
                return None
            # A model sometimes emits one line with literal \n escapes instead of real newlines.
            if "\\n" in raw_text and ("\n" not in raw_text.strip() or raw_text.count("\\n") > raw_text.count("\n") * 2):
                return raw_text.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
            return raw_text

        def _write(rel: str, body: str) -> bool:
            dest = (self.workspace_dir / rel.replace("\\", "/")).resolve()
            if ws_root != dest and ws_root not in dest.parents:
                return False  # never write outside the workspace
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
            return True

        # files: any path, several files at once (preferred shape)
        for item in llm_output.get("files") or []:
            if isinstance(item, dict):
                name = str(item.get("filename") or item.get("path") or "").strip()
                body = _normalize_raw_code(item.get("content"))
                if name and body and _write(name, body):
                    materialized_any = True

        # ast_edits: surgical symbol replacement
        for item in llm_output.get("ast_edits") or []:
            if isinstance(item, dict) and item.get("symbol") and item.get("code") is not None:
                code_str = _normalize_raw_code(str(item["code"])) or str(item["code"])
                edit_ast_node(self.workspace_dir / str(item.get("file") or node_path), str(item["symbol"]), code_str)
                materialized_any = True

        # source_code: the whole target module. Only for a Python target, so code never lands in a CSV or a thesis.
        source_code = _normalize_raw_code(llm_output.get("source_code"))
        if source_code and node_path.endswith(".py") and not materialized_any:
            materialized_any = _write(node_path, source_code)

        # test suite, results and plotting script (seed_tester)
        for body_key, file_key, default_rel in (
            ("test_code", "test_file", "test_core.py"),
            ("csv_content", "benchmark_file", "results.csv"),
            ("plot_script", "plot_file", "plot_results.py"),
        ):
            body = _normalize_raw_code(llm_output.get(body_key))
            if body and _write(str(llm_output.get(file_key) or default_rel), body):
                materialized_any = True
                if body_key == "csv_content":
                    csv_path = self.workspace_dir / str(llm_output.get(file_key) or default_rel)
                    now = time.time() + 1.0
                    os.utime(csv_path, (now, now))

        # bibliography (researchers): merged by citation key; with an arXiv-verified bibliography only its keys stay
        bibtex_entries = llm_output.get("bibtex_entries")
        verified_keys = self._verified_citation_keys()
        if isinstance(bibtex_entries, str) and bibtex_entries.strip() and verified_keys is not None:
            bibtex_entries, dropped = _filter_bibtex(bibtex_entries, verified_keys)
            if dropped:
                self._record_evolution_event({"type": "UNVERIFIED_CITATIONS_DROPPED", "keys": dropped})
        if isinstance(bibtex_entries, str) and bibtex_entries.strip():
            bib_path = self.workspace_dir / str(llm_output.get("bib_file") or "references.bib")
            existing_bib = bib_path.read_text(encoding="utf-8", errors="ignore") if bib_path.exists() else ""
            merged = _merge_bibtex_entries(existing_bib, bibtex_entries) if existing_bib else bibtex_entries.strip() + "\n"
            materialized_any = _write(bib_path.relative_to(self.workspace_dir).as_posix(), merged) or materialized_any

        if self.include_docs:
            doc_target = full_file_path if node_path.endswith((".md", ".tex")) else (self.workspace_dir / "thesis.md")

            # literature review (researchers); the discoverer extends the background section instead of replacing it
            lit_section = llm_output.get("literature_review_section")
            if isinstance(lit_section, str) and lit_section.strip():
                sec_title = str(llm_output.get("section_title") or "Analiza Stanu Wiedzy (SOTA)")
                body = lit_section
                if str(llm_output.get("research_stage") or "").strip().lower() == "discoverer" and doc_target.exists():
                    m_sec = re.search(
                        rf"^##+\s+{re.escape(sec_title)}\s*$(.*?)(?=^##\s+|\Z)",
                        doc_target.read_text(encoding="utf-8", errors="ignore"),
                        re.MULTILINE | re.DOTALL,
                    )
                    if m_sec and lit_section.strip() not in m_sec.group(1):
                        body = m_sec.group(1).strip() + "\n\n" + lit_section.strip()
                edit_document_section(doc_target, sec_title, body)
                materialized_any = True

            # thesis sections (writer): one section, or a list of sections
            sections = llm_output.get("sections") if isinstance(llm_output.get("sections"), list) else []
            # The single-section shape is used only when there is no list (an answer may carry both).
            if not sections and llm_output.get("section_title") and llm_output.get("section_content"):
                sections = [{"section_title": llm_output["section_title"], "section_content": llm_output["section_content"]}]
            for sec in sections:
                if isinstance(sec, dict):
                    title = sec.get("section_title") or sec.get("title")
                    body = sec.get("section_content") or sec.get("content")
                    if title and isinstance(body, str) and body.strip():
                        edit_document_section(doc_target, str(title), body)
                        materialized_any = True

        # An agent that returned content which landed nowhere has not done its task. Saying nothing here made a
        # discarded fix indistinguishable from an applied one.
        if not materialized_any:
            carried = sorted(k for k, v in llm_output.items() if k not in _METADATA_KEYS and v)
            if carried:
                raise MaterializationError(
                    f"Odpowiedź agenta dla '{node_path}' nie została zapisana: pola {carried} nie pasują do żadnego "
                    f"dozwolonego kształtu. Dozwolone: {OUTPUT_SCHEMA}. Pliki zwracaj w polu 'files' jako listę "
                    "{'filename', 'content'}."
                )

    def _execute_builder_step(self, task: dict[str, Any], model_tier: str) -> dict[str, Any]:
        """Invoke Layer 2 builder agent and apply deterministic Python AST / doc tools."""
        registry = read_json_state(self.registry_path).get("agents", {})
        agent_id = self._resolve_active_agent(task.get("assigned_agent"), fallback="seed_coder")
        task["assigned_agent"] = agent_id

        agent_meta = registry.get(agent_id, {})
        agent_md = self.adk_root / agent_meta.get("path", f"agents/building/{agent_id}.md")
        if not agent_md.exists():
            agent_md = self.adk_root / "agents" / "building" / "seed_coder.md"

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

        # Grounding covers the whole graph (every .py and .csv), not only the files coupled to this node.
        grounded_state: dict[str, Any] = {
            "available_figures": existing_figures,
            **build_grounded_symbols(extract_hyperedge_exports("ALL", self.matrix_path, self.workspace_dir)),
            "mandatory_directives": [
                "DO NOT invent figure paths. Only reference figures explicitly listed in 'available_figures'.",
                "For system architecture (Rozdział 3), use an INLINE TikZ environment (\\begin{tikzpicture}...\\end{tikzpicture}). NEVER reference non-existent files like figures/system_architecture.pdf.",
                "Only reference CSV columns present in 'available_csv_columns'.",
            ],
        }

        blueprint_data = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        recon_data = blueprint_data.get("literature_recon", {}) if isinstance(blueprint_data, dict) else {}
        is_doc_or_research_agent = (
            _is_document(node_path)
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
            # The metrics the plan declared (P9 pre-registration) take the place of a prescribed list.
            "standard_metrics": blueprint_data.get("metrics") or recon_data.get("standard_metrics", []),
            "canonical_baselines": recon_data.get("canonical_baselines", []),
            # The function the harness calls without arguments to run the experiment (declared in the plan).
            "academic_blueprint": {"entrypoint": blueprint_data.get("entrypoint", "")},
        }
        if is_doc_or_research_agent:
            builder_payload["thesis_type"] = blueprint_data.get("thesis_type", "inzynierska")
            builder_payload["template_name"] = blueprint_data.get("template_name", "thesis_plodz")
            builder_payload["table_of_contents"] = blueprint_data.get("table_of_contents", {})
            builder_payload["available_citation_keys"] = recon_data.get("available_citation_keys", [])
            builder_payload["sampled_methodologies"] = recon_data.get("sampled_methodologies", [])

        llm_res = self._call_agent(
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

    def _refresh_experiment_after_code(self, node_id: str) -> None:
        """After any change to Python code, results are whatever the experiment pipeline just wrote."""
        node_path = str(read_json_state(self.matrix_path).get("nodes", {}).get(node_id, {}).get("path", node_id))
        touched_code = node_path.endswith(".py") or self._role_of(node_id) == "results"
        if str(self.provider).strip().lower() == "mock" or not touched_code:
            return
        from adk.tools.building.experiment_runner import execute_workspace_experiment

        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        entrypoint = str(blueprint.get("entrypoint") or "").strip() if isinstance(blueprint, dict) else ""
        result = execute_workspace_experiment(self.workspace_dir, entrypoint=entrypoint or None)
        if result.get("skipped") or result.get("ok"):
            self._last_experiment_error = ""
            return
        self._last_experiment_error = str(result.get("error") or "Eksperyment nie wygenerował results.csv")
