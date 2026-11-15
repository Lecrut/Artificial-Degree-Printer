"""Layer 2: run a builder agent and write its output to the workspace."""

from __future__ import annotations


import ast
import os
import re
import time
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, write_json_state
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
from adk.tools.building.hypergraph_sync import ensure_node
from adk.tools.verification.contract_check import (
    interface_contract_breaches,
    interface_contract_extensions,
    is_contract_module,
    public_api,
)
from adk.tools.verification.test_runner import iter_workspace_python_files
from adk.orchestration.common import (
    _agent_for_path,
    available_package_imports,
    _collect_report_issues,
    _filter_bibtex,
    _merge_bibtex_entries,
    _is_document,
    MaterializationError,
    OUTPUT_SCHEMA,
    _METADATA_KEYS,
    build_grounded_symbols,
    is_skeleton_task,
)

# pytest summary line: `FAILED path.py::Class::test_name - message` (or ERROR)
_FAILED_TEST_LINE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+?\.py)::(\S+?)(?:\s+-\s+(.*))?$", re.MULTILINE)


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


def _symbol_source(source: str | None, symbol: str) -> str | None:
    """Source text of a top-level function/class or `Class.method` in `source`; None when absent or unparsable."""
    if not source:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    cls_name, _, member = symbol.rpartition(".")
    body: list[ast.stmt] = tree.body
    if cls_name:
        owner = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls_name), None)
        if owner is None:
            return None
        body = owner.body
    name = member if cls_name else symbol
    node = next(
        (n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name),
        None,
    )
    return ast.get_source_segment(source, node) if node is not None else None


def _test_function_source(path: Path, qualname: str) -> str | None:
    """Source of `Class::test` or `test` (parametrization suffix ignored) in a test file."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError, ValueError):
        return None
    scope: list[ast.stmt] = tree.body
    node: ast.stmt | None = None
    for part in [p.split("[")[0] for p in qualname.split("::")]:
        node = next((n for n in scope if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == part), None)
        if node is None:
            return None
        scope = node.body if isinstance(node, ast.ClassDef) else []
    return ast.get_source_segment(source, node) if node is not None else None


class BuildingMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    @property
    def interface_contract_path(self) -> Path:
        return self.state_dir / "interface_contract.json"

    def _materialize_workspace_artifact(
        self,
        node_path: str,
        llm_output: dict[str, Any],
        establishes_contract: bool = False,
        writer: dict[str, Any] | None = None,
    ) -> None:
        """Write a builder's output to the workspace. Accepted shapes are listed in OUTPUT_SCHEMA; an answer that
        carries content in none of them is an error returned to the agent, never a silent no-op.

        An answer is applied as a whole or not at all: a failed symbol edit or an unexplained change of the
        interface contract restores every file the answer touched and raises MaterializationError.
        `writer` (`{agent, task_id}`) is remembered on every node written, so a later failure in that file is
        charged to its author, not to whichever task happened to run the verification (R5)."""
        originals: dict[Path, str | None] = {}
        try:
            self._apply_builder_output(node_path, llm_output, originals, str((writer or {}).get("agent") or ""))
            self._enforce_interface_contract(originals, llm_output, establishes_contract, node_path)
        except MaterializationError:
            for dest, before in originals.items():
                if before is None:
                    dest.unlink(missing_ok=True)
                else:
                    dest.write_text(before, encoding="utf-8")
            raise
        plot_name = str(llm_output.get("plot_file") or "plot_results.py").replace("\\", "/")
        self._record_written(node_path, originals, writer, establishes_contract, plot_name)

    def _record_written(
        self,
        node_path: str,
        originals: dict[Path, str | None],
        writer: dict[str, Any] | None,
        skeleton: bool,
        plot_name: str = "plot_results.py",
    ) -> None:
        """Remember who wrote which files (node `last_writer`) and queue them for the next verification's scope.
        Two kinds of write are logged, not blocked (R6; the hard ban of Q12 waits for a measurement):
        `OFF_TARGET_WRITE` — outside the task's node and its hyperedge neighbours;
        `CROSS_ROLE_WRITE` — a Python file of the other role (a coder's test, a tester's module)."""
        ws_root = self.workspace_dir.resolve()
        written = sorted(dest.relative_to(ws_root).as_posix() for dest in originals if dest.exists())
        if not written:
            return
        pending: set[str] = getattr(self, "_written_since_verification", set())
        pending.update(written)
        self._written_since_verification = pending
        if not Path(self.matrix_path).exists():
            return  # no hypergraph yet (bare state directory): nothing to annotate
        for rel in written:
            ensure_node(rel, self.matrix_path)
        data = read_json_state(self.matrix_path)
        nodes: dict[str, dict[str, Any]] = data.get("nodes", {})
        by_path = {str(meta.get("path", "")): node_id for node_id, meta in nodes.items()}
        if writer:
            for rel in written:
                nodes[by_path[rel]]["last_writer"] = dict(writer)
            write_json_state(self.matrix_path, data)
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
        if skeleton:
            return
        own = by_path.get(node_path)
        allowed = {node_path}
        for members in data.get("edges", {}).values():
            if own in members:
                allowed.update(str(nodes.get(m, {}).get("path", "")) for m in members)
        off_target = [rel for rel in written if rel not in allowed]
        if off_target:
            self._record_evolution_event(
                {"type": "OFF_TARGET_WRITE", "node": node_path, "files": off_target, **writer}
            )

    def _enforce_interface_contract(
        self, originals: dict[Path, str | None], llm_output: dict[str, Any], establishes_contract: bool, node_path: str = ""
    ) -> None:
        """After the skeleton task the public signatures of code modules are the contract between tasks.
        Changing or removing one needs `contract_change: {reason}`; new public symbols join the contract freely.

        A breach in a file that is NOT the task's target restores that one file and keeps the rest of the
        answer: on 2026-11-14 the tester attached `plot_script` to every test repair, broke `plot_results.py`'s
        contract, and ~95 whole answers — including the corrected tests — were thrown away for it."""
        ws_root = self.workspace_dir.resolve()
        if establishes_contract:
            contract: dict[str, dict[str, list[str]]] = {}
            for path in iter_workspace_python_files(self.workspace_dir):
                rel = path.resolve().relative_to(ws_root).as_posix()
                api = public_api(path.read_text(encoding="utf-8", errors="replace")) if is_contract_module(rel) else None
                if api:
                    contract[rel] = api
            write_json_state(self.interface_contract_path, contract)
            self._record_evolution_event({"type": "CONTRACT_ESTABLISHED", "files": sorted(contract)})
            return
        if not self.interface_contract_path.exists():
            return
        contract = read_json_state(self.interface_contract_path)
        touched = {
            dest.relative_to(ws_root).as_posix(): dest
            for dest in originals
            if dest.exists() and is_contract_module(dest.relative_to(ws_root).as_posix())
        }
        change = llm_output.get("contract_change")
        reason = str(change.get("reason") if isinstance(change, dict) else change or "").strip()
        breaches_by_rel = {
            rel: interface_contract_breaches(contract, rel, dest.read_text(encoding="utf-8", errors="replace"))
            for rel, dest in touched.items()
        }
        if not reason:
            protected = [rel for rel, found in breaches_by_rel.items() if found and rel != node_path]
            for rel in protected:
                dest = touched.pop(rel)
                before = originals.pop(dest, None)
                if before is None:
                    dest.unlink(missing_ok=True)
                else:
                    dest.write_text(before, encoding="utf-8")
                breaches_by_rel.pop(rel)
            if protected:
                self._record_evolution_event(
                    {"type": "CONTRACT_FILE_RESTORED", "node": node_path, "files": sorted(protected)}
                )
        breaches = [breach for found in breaches_by_rel.values() for breach in found]
        if breaches and not reason:
            # The small model rewriting a whole file loses skeleton symbols; without their source the retry
            # could only guess them back (2026-11-14: 38+ such rejections).
            help_sources = self._removed_symbol_sources(originals, breaches)
            raise MaterializationError(
                "Zapis odrzucony: zmienia publiczne sygnatury ustalone w szkielecie (kontrakt między zadaniami):\n- "
                + "\n- ".join(breaches)
                + "\nAlbo zachowaj te sygnatury i zmień tylko implementację, albo dodaj do odpowiedzi "
                "'contract_change': {'reason': '<dlaczego API musi się zmienić>'}. Moduły, które z niego korzystają, "
                "dostosuje się w kolejnych zadaniach."
                + help_sources
            )
        # Placeholder signatures filled in with their first parameters: allowed, but on record (N6).
        extensions = [
            ext
            for rel, dest in touched.items()
            for ext in interface_contract_extensions(contract, rel, dest.read_text(encoding="utf-8", errors="replace"))
        ]
        for rel, dest in touched.items():
            if breaches_by_rel.get(rel) and not reason:
                continue
            api = public_api(dest.read_text(encoding="utf-8", errors="replace"))
            if api is not None:
                contract[rel] = {**contract.get(rel, {}), **api} if not breaches else api
        write_json_state(self.interface_contract_path, contract)
        if breaches:
            self._record_evolution_event({"type": "CONTRACT_CHANGED", "changes": breaches, "reason": reason})
        if extensions:
            self._record_evolution_event(
                {"type": "CONTRACT_CHANGED", "changes": extensions, "reason": "uzupełnienie sygnatury zastępczej ze szkieletu"}
            )

    @staticmethod
    def _removed_symbol_sources(originals: dict[Path, str | None], breaches: list[str], budget: int = 2000) -> str:
        """Source of the symbols a breach says were removed, taken from the file's previous version, so the
        retry can paste them back instead of guessing."""
        found: list[str] = []
        used = 0
        for breach in breaches:
            m = re.match(r"^(.+?): (?:usunięto )?([\w.]+)\(", breach)
            if not m:
                continue
            rel, symbol = m.group(1), m.group(2)
            before = next((txt for dest, txt in originals.items() if txt and dest.name == Path(rel).name), None)
            source = _symbol_source(before, symbol)
            if source and used + len(source) <= budget:
                found.append(f"# {rel}: {symbol}\n{source}")
                used += len(source)
        if not found:
            return ""
        return "\nKod tych symboli z poprzedniej wersji pliku (wklej je z powrotem):\n" + "\n\n".join(found)

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
            return rel

        def _is_test_rel(rel: str) -> bool:
            name = Path(rel).name
            return rel.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))

        # One file answered flat (`{filename, content}`) is the `files` shape with one element.
        flat_name = llm_output.get("filename") or llm_output.get("path")
        if not llm_output.get("files") and flat_name and isinstance(llm_output.get("content"), str):
            llm_output = {**llm_output, "files": [{"filename": flat_name, "content": llm_output["content"]}]}

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
                raise MaterializationError(
                    "Kod nie parsuje się; nic z tej odpowiedzi nie zapisano. Popraw wskazane miejsca i zwróć odpowiedź "
                    "ponownie w tym samym formacie:\n- " + "\n- ".join(syntax_errors)
                )

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
                edit_errors.append(
                    f"element ast_edits bez wymaganego 'symbol' albo 'code' (ma klucze: {sorted(item)}); "
                    "każdy element to {'symbol': '<nazwa lub Klasa.metoda>', 'code': '<kod>', 'file': '<ścieżka.py>'}"
                )
                continue
            if isinstance(item, dict) and item.get("symbol") and item.get("code") is not None:
                code_str = _normalize_raw_code(str(item["code"])) or str(item["code"])
                symbol, named_file = _plain_symbol(str(item["symbol"]))
                file_rel = _canonical(str(item.get("file") or named_file or node_path))
                if not file_rel.endswith(".py"):
                    # N7: `ast_edits` on thesis.md answered "SyntaxError in new_code", which told the writer nothing.
                    edit_errors.append(
                        f"{file_rel}: 'ast_edits' działa tylko dla plików .py. Pracę zmieniaj przez 'sections' "
                        "([{section_title, section_content}]), inne pliki przez 'files'."
                    )
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
                    if _write(edit_path.relative_to(ws_root).as_posix(), code_str):
                        materialized_any = True
                    continue
                _remember(edit_path)
                result = edit_ast_node(edit_path, symbol, code_str)
                if result.get("status") == "ok":
                    materialized_any = True
                elif str(result.get("error", "")).startswith("Existing file has SyntaxError"):
                    # A symbol edit has no tree to land in. The only way out is the whole file, so say so.
                    rel = edit_path.relative_to(ws_root).as_posix()
                    edit_errors.append(
                        f"{rel}: plik jest obecnie nieparsowalny ({result['error'].removeprefix('Existing file has SyntaxError: ')}), "
                        f"więc edycja symbolu {item['symbol']} nie ma do czego trafić. Zwróć cały poprawiony plik "
                        f"w 'files' (filename: '{rel}'), a nie w 'ast_edits'."
                    )
                else:
                    edit_errors.append(f"{edit_path.name}:{item['symbol']}: {result.get('error')}")
        _raise_if_unparsable()
        if edit_errors:
            raise MaterializationError("Edycje symboli odrzucone (nic z tej odpowiedzi nie zapisano):\n- " + "\n- ".join(edit_errors))

        # source_code: the whole target module. Only for a Python target, so code never lands in a CSV or a thesis.
        source_code = _normalize_raw_code(llm_output.get("source_code"))
        if source_code and node_path.endswith(".py") and not materialized_any:
            materialized_any = _write(node_path, source_code)

        # test suite, results and plotting script (seed_tester). A side artifact lands only when it IS the
        # task's target (same path or name) or does not exist yet: on 2026-11-14 the tester attached
        # `plot_script` to every test repair and the stale script overwrote `plot_results.py` each time.
        skipped_side: list[str] = []
        for body_key, file_key, default_rel in (
            ("test_code", "test_file", "test_core.py"),
            ("csv_content", "benchmark_file", "results.csv"),
            ("plot_script", "plot_file", "plot_results.py"),
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
                        _remember(doc_target)
                        edit_document_section(doc_target, str(title), body)
                        materialized_any = True

        # An agent that returned content which landed nowhere has not done its task. Saying nothing here made a
        # discarded fix indistinguishable from an applied one.
        if not materialized_any:
            if role_skipped:
                raise MaterializationError(
                    f"Zapis odrzucony: pliki testów ({', '.join(sorted(set(role_skipped)))}) należą do testera i koder "
                    "ich nie zmienia. Popraw kod modułu tak, żeby test przechodził. Jeśli uważasz, że to test jest "
                    "błędny, napisz to w 'summary' (co i dlaczego) — następna naprawa trafi do testera."
                )
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
                "Draw an architecture diagram inline (TikZ or Mermaid, small) instead of referencing a figure file that does not exist.",
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
            # One source of truth for external imports (D2): the canonical import line of every package this
            # fixed environment provides. Anything else is unavailable for the whole run (D1).
            "available_packages": available_package_imports(),
            # The metrics the plan declared (P9 pre-registration) take the place of a prescribed list.
            "standard_metrics": blueprint_data.get("metrics") or recon_data.get("standard_metrics", []),
            "canonical_baselines": recon_data.get("canonical_baselines", []),
            # The function the harness calls without arguments to run the experiment (declared in the plan).
            "academic_blueprint": {"entrypoint": blueprint_data.get("entrypoint", "")},
        }
        # A repair sees the tests it has to satisfy, not only a prose summary of their failure.
        if task.get("repair_of") and not is_doc_or_research_agent:
            failing = self._failing_test_sources()
            if failing:
                builder_payload["failing_tests"] = failing
        if is_doc_or_research_agent:
            builder_payload["thesis_type"] = blueprint_data.get("thesis_type", "inzynierska")
            builder_payload["template_name"] = blueprint_data.get("template_name", "thesis_plodz")
            builder_payload["table_of_contents"] = blueprint_data.get("table_of_contents", {})
            builder_payload["available_citation_keys"] = recon_data.get("available_citation_keys", [])
            builder_payload["sampled_methodologies"] = recon_data.get("sampled_methodologies", [])

        writer = {"agent": agent_id, "task_id": str(task.get("task_id", ""))}
        llm_res = self._call_agent(agent_md, builder_payload, model_tier=model_tier, provider=self.provider)
        try:
            self._materialize_workspace_artifact(
                node_path, llm_res.get("output", {}), establishes_contract=is_skeleton_task(task), writer=writer
            )
        except MaterializationError as exc:
            # A rejected answer (unparsable code, wrong shape, unexplained contract change) is deterministic and
            # self-describing, so the same agent gets the exact message once, right away, before any planner or
            # evolution call (Audit I §5.4 / R7). A second rejection goes the regular way.
            self.logger.log_step(
                "BUILDING_RETRY",
                f"Odpowiedź dla zadania {task.get('task_id')} odrzucona; natychmiastowe ponowienie u '{agent_id}'",
                {"error": str(exc)[:2000]},
            )
            self._record_evolution_event(
                {"type": "BUILDER_ANSWER_REJECTED", "task_id": task.get("task_id"), "agent": agent_id, "error": str(exc)[:2000]}
            )
            retry_payload = {
                **builder_payload,
                "rejected_answer": {
                    "error": str(exc),
                    "instruction": (
                        "Twoja poprzednia odpowiedź została odrzucona i nic z niej nie zapisano. Usuń przyczynę opisaną "
                        "w 'error' i zwróć poprawioną odpowiedź w tym samym formacie."
                    ),
                },
            }
            llm_res = self._call_agent(agent_md, retry_payload, model_tier=model_tier, provider=self.provider)
            self._materialize_workspace_artifact(
                node_path, llm_res.get("output", {}), establishes_contract=is_skeleton_task(task), writer=writer
            )
        sync_hypergraph_matrix(self.workspace_dir, self.matrix_path)
        return llm_res

    def _failing_test_sources(self, limit: int = 6, budget: int = 6000) -> dict[str, dict[str, str]]:
        """`file::Class::test` -> {error, source} for the failing tests of the last verification report."""
        report = read_json_state(self.validation_report_path) if self.validation_report_path.exists() else {}
        if report.get("status") != "FAIL":
            return {}
        found: dict[str, dict[str, str]] = {}
        used = 0
        for match in _FAILED_TEST_LINE.finditer("\n".join(_collect_report_issues(report))):
            rel, qualname, error = match.group(1), match.group(2), (match.group(3) or "").strip()
            key = f"{Path(rel).name}::{qualname}"
            if key in found:
                continue
            candidates = (self.workspace_dir / rel, self.workspace_dir / Path(rel).name)
            path = next((p for p in candidates if p.is_file()), None)
            source = _test_function_source(path, qualname) if path else None
            if not source or used + len(source) > budget:
                continue
            found[key] = {"error": error[:300], "source": source}
            used += len(source)
            if len(found) >= limit:
                break
        return found

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
