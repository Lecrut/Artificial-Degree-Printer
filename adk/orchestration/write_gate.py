"""Write gate: a builder's answer is written to the workspace as a whole or not at all, and its author is recorded."""

from __future__ import annotations


import ast
import os
import re
import time
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state
from adk.hypergraph import save
from adk.hypergraph.schedule import vertex_of
from adk.tools.building import (
    edit_ast_node,
    edit_document_section,
)
from adk.tools.building.ast_editor import declared_names, split_existing_symbols, whole_module_loss
from adk.tools.building.doc_editor import split_section_title
from adk.orchestration.common import (
    _normalized_files,
    _agent_for_path,
    _filter_bibtex,
    _merge_bibtex_entries,
    MaterializationError,
    OUTPUT_SCHEMA,
    THESIS_FILE,
    _METADATA_KEYS,
)


def _plain_symbol(raw: str) -> tuple[str, str | None]:
    """`path/to/file.py:Class.method` -> (`Class.method`, `path/to/file.py`); `pkg/mod.func` -> (`mod.func`, None);
    `src/exp/runner.py.run_all` -> (`run_all`, `src/exp/runner.py`); a leading `class ` / `def ` is dropped."""
    raw = raw.strip().replace("\\", "/")
    named_file = None
    if ":" in raw:
        head, _, raw = raw.rpartition(":")
        named_file = head if head.endswith(".py") else None
    if ".py." in raw:
        head, raw = raw.split(".py.", 1)
        named_file = named_file or f"{head}.py"
    if "/" in raw:
        raw = raw.rsplit("/", 1)[1]
    raw = re.sub(r"^(?:class|def)\s+", "", raw)
    if raw.endswith(".py") and raw.count(".") == 1:
        return raw, named_file
    return raw.removesuffix(".py"), named_file


class WriteGateMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _materialize_workspace_artifact(
        self,
        node_path: str,
        llm_output: dict[str, Any],
        writer: dict[str, Any] | None = None,
    ) -> None:
        """Write a builder's output to the workspace. Accepted shapes are listed in OUTPUT_SCHEMA; an answer that
        carries content in none of them is an error returned to the agent, never a silent no-op.

        An answer is applied as a whole or not at all: a failed symbol edit or a breach of the specification σ
        restores every file the answer touched and raises MaterializationError.
        `writer` (`{agent, task_id}`) is remembered on every node written, so a later failure in that file is
        charged to its author, not to whichever task happened to run the verification (R5)."""
        originals: dict[Path, str | None] = {}
        try:
            self._apply_builder_output(node_path, llm_output, originals, str((writer or {}).get("agent") or ""))
            self._enforce_spec_on_write(originals, llm_output)  # σ in the project hypergraph is the contract (A5)
        except MaterializationError:
            for dest, before in originals.items():
                if before is None:
                    dest.unlink(missing_ok=True)
                else:
                    dest.write_text(before, encoding="utf-8")
            raise
        plot_name = str(llm_output.get("plot_file") or node_path).replace("\\", "/")
        self._record_written(node_path, originals, writer, plot_name)

    def _planned_names(self, rel: str) -> set[str] | None:
        """Names the plan's interface declares for module `rel` (None: the plan has no interface for it)."""
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        interfaces = blueprint.get("interfaces") if isinstance(blueprint, dict) else None
        source = interfaces.get(rel) if isinstance(interfaces, dict) else None
        try:
            return declared_names(str(source)) if source else None
        except SyntaxError:
            return None

    def _record_written(
        self,
        node_path: str,
        originals: dict[Path, str | None],
        writer: dict[str, Any] | None,
        plot_name: str = "",
    ) -> None:
        """Remember who wrote which files (`last_writer` on their vertex in H) and queue them for the next
        verification's scope. Two kinds of write are logged, not blocked (R6):
        `OFF_TARGET_WRITE` — outside the task's vertex and the members of its bags;
        `CROSS_ROLE_WRITE` — a Python file of the other role (a coder's test, a tester's module)."""
        ws_root = self.workspace_dir.resolve()
        written = sorted(dest.relative_to(ws_root).as_posix() for dest in originals if dest.exists())
        if not written:
            return
        pending: set[str] = getattr(self, "_written_since_verification", set())
        pending.update(written)
        self._written_since_verification = pending
        h = self._project_h()
        if h is not None and writer:
            for rel in written:
                owner = h.owner_of(rel)
                if owner is not None:
                    h.vertices[owner].last_writer = dict(writer)
            save(h, self.hypergraph_path)
        if h is not None and THESIS_FILE in written:
            self._record_citations()
        if not writer:
            return
        agent = str(writer.get("agent") or "")
        if agent.startswith(("seed_coder", "seed_tester", "seed_writer")):
            cross_role = [
                rel
                for rel in written
                if rel.endswith(".py")
                and not agent.startswith(_agent_for_path(rel))
                and not (agent.startswith("seed_tester") and rel == plot_name)
            ]
            if cross_role:
                self._record_evolution_event(
                    {"type": "CROSS_ROLE_WRITE", "node": node_path, "files": cross_role, **writer}
                )
        if agent == "harness" or h is None:
            return  # the stubs of every planned module, written from σ; without a plan there are no bags
        own = h.owner_of(node_path) or vertex_of(h, node_path, "")
        # A thesis task belongs to the chapters' bags: the bibliography and research files they cite are its own.
        owns = {own} if own else {v for v in h.vertices if node_path == THESIS_FILE and v.startswith(f"{THESIS_FILE}#ch")}
        allowed = {node_path}
        for edge in h.edges.values():
            if edge.type != "S" and owns & set(edge.members):
                allowed.update(f for member in edge.members if member in h.vertices for f in h.files_of(member))
        off_target = [rel for rel in written if rel not in allowed and h.owner_of(rel) not in (*owns, None)]
        if off_target:
            self._record_evolution_event(
                {"type": "OFF_TARGET_WRITE", "node": node_path, "files": off_target, **writer}
            )

    def _apply_builder_output(
        self, node_path: str, llm_output: dict[str, Any], originals: dict[Path, str | None], agent: str = ""
    ) -> None:
        full_file_path = self.workspace_dir / node_path
        materialized_any = False
        ws_root = self.workspace_dir.resolve()
        syntax_errors: list[str] = []
        # Test files a coder tried to write: skipped, the rest of the answer kept (N2, 2026-11-15: once a failed
        # assertion became the code's fault, the coder "fixed" it 7 times by rewriting the test instead).
        role_skipped: list[str] = []
        coder = agent.startswith("seed_coder")

        def _canonical(rel: str) -> str:
            """Workspace-relative path as the agent meant it (N3, 2026-11-15): a leading `workspace/` or `./` is the
            agent naming the workspace itself (it created `workspace/workspace/tests/...`), and a test file whose
            basename already exists in exactly one place goes there instead of becoming a duplicate
            (`test_experiment.py` next to `tests/test_experiment.py`)."""
            rel = rel.replace("\\", "/").strip()
            # a path through the sandbox (copied from a tool message) means the file in the workspace
            rel = rel.rsplit("/workspace/", 1)[-1]
            while rel.startswith(("./", "workspace/")):
                rel = rel.removeprefix("./").removeprefix("workspace/")
            name = Path(rel).name
            if (name.startswith("test_") or name.endswith("_test.py")) and not (self.workspace_dir / rel).exists():
                same = [
                    p for p in self.workspace_dir.rglob(name)
                    if p.is_file() and "__pycache__" not in p.parts and "logs" not in p.relative_to(self.workspace_dir).parts
                ]
                if len(same) == 1:
                    return same[0].relative_to(self.workspace_dir).as_posix()
                if "/" not in rel and Path(node_path).name == name:
                    return node_path  # the task's own test module, named without its directory (U4: tests/...)
            return rel

        def _is_test_rel(rel: str) -> bool:
            name = Path(rel).name
            return rel.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))

        llm_output = _normalized_files(llm_output)

        def _remember(dest: Path) -> None:
            dest = dest.resolve()
            if dest not in originals:
                originals[dest] = dest.read_text(encoding="utf-8", errors="replace") if dest.exists() else None

        def _normalize_raw_code(raw_text: Any) -> str | None:
            if not isinstance(raw_text, str) or not raw_text.strip():
                return None
            # A model sometimes emits one line with literal \n escapes instead of real newlines.
            if "\\n" in raw_text and ("\n" not in raw_text.strip() or raw_text.count("\\n") > raw_text.count("\n") * 2):
                return raw_text.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
            return raw_text

        def _syntax_error(rel: str, body: str) -> str | None:
            """`file:line: message` with the surrounding lines, or None for a non-Python file or valid code."""
            if not rel.endswith(".py"):
                return None
            try:
                ast.parse(body, filename=rel)
            except SyntaxError as exc:
                lines = body.splitlines()
                ln = exc.lineno or 1
                context = "\n".join(f"  {n + 1:>4}: {lines[n]}" for n in range(max(0, ln - 2), min(len(lines), ln + 1)))
                return f"{rel}:{ln}: {exc.msg}\n{context}"
            return None

        def _write(rel: str, body: str) -> bool:
            rel = _canonical(rel)
            if coder and _is_test_rel(rel):
                role_skipped.append(rel)
                return False
            dest = (self.workspace_dir / rel).resolve()
            if ws_root != dest and ws_root not in dest.parents:
                return False  # never write outside the workspace
            # Unparsable Python never reaches the disk: a file written broken could not be repaired by symbol
            # edits afterwards and blocked every later task (2026-11-13: three modules lost for the whole run).
            problem = _syntax_error(rel.replace("\\", "/"), body)
            if problem:
                syntax_errors.append(problem)
                return False
            _remember(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
            return True

        def _raise_if_unparsable() -> None:
            if syntax_errors:
                raise MaterializationError(texts.unparsable_code(syntax_errors))

        # files: any path, several files at once (preferred shape). An empty file (`__init__.py`) is a file.
        for item in llm_output.get("files") or []:
            if isinstance(item, dict):
                name = str(item.get("filename") or item.get("path") or "").strip()
                raw = item.get("content")
                body = _normalize_raw_code(raw) if isinstance(raw, str) and raw.strip() else ("" if isinstance(raw, str) else None)
                if name and body is not None and _write(name, body):
                    materialized_any = True
        _raise_if_unparsable()

        # ast_edits: surgical symbol replacement (`name` or `Class.method`). A rejected edit is an error for the
        # agent, not a silently skipped change.
        edit_errors: list[str] = []
        for item in llm_output.get("ast_edits") or []:
            if isinstance(item, dict) and not (item.get("symbol") and item.get("code") is not None):
                # N7: a malformed element used to vanish and surface as "fields ['ast_edits'] match no shape".
                edit_errors.append(texts.malformed_ast_edit(sorted(item)))
                continue
            if isinstance(item, dict) and item.get("symbol") and item.get("code") is not None:
                code_str = _normalize_raw_code(str(item["code"])) or str(item["code"])
                symbol, named_file = _plain_symbol(str(item["symbol"]))
                file_rel = _canonical(str(item.get("file") or named_file or node_path))
                if not file_rel.endswith(".py"):
                    # N7: `ast_edits` on thesis.md answered "SyntaxError in new_code", which told the writer nothing.
                    edit_errors.append(texts.ast_edits_not_python(file_rel))
                    continue
                if coder and _is_test_rel(file_rel):
                    role_skipped.append(file_rel)
                    continue
                edit_path = (self.workspace_dir / file_rel).resolve()
                if ws_root != edit_path and ws_root not in edit_path.parents:
                    continue
                # The model qualifies symbols the way it reads them: `random_agent.RandomAgent.__init__`,
                # `src/experiment/runner.run_all`, `tests.test_config.X`. Module/path parts of the target file are
                # not part of the symbol (2026-11-14: ~30 rejected edits). A bare file name means the whole file.
                parts = symbol.split(".")
                rel_parts = set(edit_path.relative_to(ws_root).with_suffix("").parts)
                while len(parts) > 1 and parts[0] in rel_parts:
                    parts.pop(0)
                symbol = ".".join(parts)
                if not symbol or symbol in (edit_path.name, edit_path.stem):
                    lost = whole_module_loss(edit_path.read_text(encoding="utf-8"), code_str) if edit_path.exists() else []
                    if lost:
                        edit_errors.append(texts.whole_module_loses_symbols(edit_path.name, str(item["symbol"]), lost))
                        continue
                    if _write(edit_path.relative_to(ws_root).as_posix(), code_str):
                        materialized_any = True
                    continue
                _remember(edit_path)
                pieces = split_existing_symbols(code_str, edit_path) if "." not in symbol else None
                for piece_symbol, piece_code in pieces or [(symbol, code_str)]:
                    result = edit_ast_node(edit_path, piece_symbol, piece_code, planned=self._planned_names(file_rel))
                    if result.get("status") == "ok":
                        materialized_any = True
                    elif str(result.get("error", "")).startswith("Existing file has SyntaxError"):
                        # A symbol edit has no tree to land in. The only way out is the whole file, so say so.
                        rel = edit_path.relative_to(ws_root).as_posix()
                        edit_errors.append(
                            texts.edit_on_unparsable_file(rel, result["error"].removeprefix("Existing file has SyntaxError: "), item["symbol"])
                        )
                        break
                    else:
                        edit_errors.append(f"{edit_path.name}:{piece_symbol}: {result.get('error')}")
        _raise_if_unparsable()
        if edit_errors:
            raise MaterializationError(texts.symbol_edits_rejected(edit_errors))

        # source_code: the whole target module. Only for a Python target, so code never lands in a CSV or a thesis.
        source_code = _normalize_raw_code(llm_output.get("source_code"))
        if source_code and node_path.endswith(".py") and not materialized_any:
            materialized_any = _write(node_path, source_code)

        # test suite, results and plotting script (seed_tester). A side artifact lands only when it IS the
        # task's target (same path or name) or does not exist yet: on 2026-11-14 the tester attached
        # `plot_script` to every test repair and the stale script overwrote the plotting module each time.
        skipped_side: list[str] = []
        for body_key, file_key, default_rel in (
            ("test_code", "test_file", node_path),  # without a file name: the task's own target (§XIII)
            ("csv_content", "benchmark_file", "results.csv"),
            ("plot_script", "plot_file", node_path),
        ):
            body = _normalize_raw_code(llm_output.get(body_key))
            side_rel = _canonical(str(llm_output.get(file_key) or default_rel))
            if body and (
                side_rel != node_path
                and Path(side_rel).name != Path(node_path).name
                and (self.workspace_dir / side_rel).exists()
            ):
                skipped_side.append(f"{body_key} -> {side_rel}")
                continue
            if body and _write(side_rel, body):
                materialized_any = True
                if body_key == "csv_content":
                    csv_path = self.workspace_dir / side_rel
                    now = time.time() + 1.0
                    os.utime(csv_path, (now, now))
        if skipped_side:
            self._record_evolution_event({"type": "SIDE_ARTIFACT_SKIPPED", "node": node_path, "skipped": skipped_side})
        _raise_if_unparsable()
        if role_skipped:
            self._record_evolution_event(
                {"type": "CODER_TEST_WRITE_SKIPPED", "node": node_path, "agent": agent, "files": sorted(set(role_skipped))}
            )

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
                sec_title, body = split_section_title(str(llm_output.get("section_title") or "Analiza Stanu Wiedzy (SOTA)"), lit_section)
                lit_section = body = self._known_citations_only(body)
                if str(llm_output.get("research_stage") or "").strip().lower() == "discoverer" and doc_target.exists():
                    m_sec = re.search(
                        rf"^##+\s+{re.escape(sec_title)}\s*$(.*?)(?=^##\s+|\Z)",
                        doc_target.read_text(encoding="utf-8", errors="ignore"),
                        re.MULTILINE | re.DOTALL,
                    )
                    if m_sec and lit_section.strip() not in m_sec.group(1):
                        body = m_sec.group(1).strip() + "\n\n" + lit_section.strip()
                _remember(doc_target)
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
                        title, body = split_section_title(str(title), body)
                        body = self._known_citations_only(body)
                        _remember(doc_target)
                        edit_document_section(doc_target, str(title), body)
                        materialized_any = True

        # An agent that returned content which landed nowhere has not done its task. Saying nothing here made a
        # discarded fix indistinguishable from an applied one.
        if not materialized_any:
            if role_skipped:
                raise MaterializationError(texts.tests_belong_to_tester(role_skipped))
            carried = sorted(k for k, v in llm_output.items() if k not in _METADATA_KEYS and v)
            if carried:
                raise MaterializationError(texts.unknown_answer_shape(node_path, carried, OUTPUT_SCHEMA))
