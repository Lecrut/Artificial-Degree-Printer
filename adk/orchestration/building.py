"""Layer 2: run a builder agent and write its output to the workspace."""

from __future__ import annotations


import ast
import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state
from adk.orchestration.common import (
    THESIS_FILE,
    available_package_imports,
    _collect_report_issues,
    _is_document,
    MaterializationError,
)

# pytest summary line: `FAILED path.py::Class::test_name - message` (or ERROR)
_FAILED_TEST_LINE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+?\.py)::(\S+?)(?:\s+-\s+(.*))?$", re.MULTILINE)


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


_POINTER = re.compile(r"\\ref_(?:ast|csv|fig)\{[^}]*\}")
DOC_CONTEXT_BUDGET = 6000


def _document_context(document: str, task_description: str) -> str:
    """The outline of a long document plus the part the task works on: the whole target chapter, or the chapters
    holding the pointers the task names, or (neither) the end of the document. 2026-11-15: a chapter was cut to
    1500 characters before "replace the section", and CRITIC tasks fixing pointers saw only the last 600
    characters, never the chapters with the pointers (13 failed attempts in Q2-Q4)."""
    from adk.tools.building.doc_editor import _extract_canonical_chapter_num

    outline = "\n".join(
        [line for line in document.splitlines() if line.strip().startswith(("#", "\\chapter", "\\section", "\\subsection"))][:30]
    )
    heads = list(re.finditer(r"^##\s+([^\n]+)$", document, flags=re.MULTILINE))
    chapters = [
        (_extract_canonical_chapter_num(m.group(1)), document[m.start() : heads[i + 1].start() if i + 1 < len(heads) else len(document)].strip())
        for i, m in enumerate(heads)
    ]
    target = _extract_canonical_chapter_num(task_description)
    pointers = set(_POINTER.findall(task_description))
    if target is not None:
        parts, label = [text for number, text in chapters if number == target], texts.chapter_context_label(target)
    elif pointers:
        parts, label = [text for _, text in chapters if any(p in text for p in pointers)], texts.POINTER_CHAPTERS_LABEL
    else:
        parts, label = [], ""
    body = "\n\n".join(parts)
    if not body:
        body, label = document[-600:], texts.DOCUMENT_TAIL_LABEL
    elif len(body) > DOC_CONTEXT_BUDGET:
        body = body[:DOC_CONTEXT_BUDGET] + texts.clipped(len(body) - DOC_CONTEXT_BUDGET)
    return f"{texts.DOCUMENT_OUTLINE_LABEL}\n{outline}\n\n{label}\n{body}"


class BuildingMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""


    def _execute_builder_step(self, task: dict[str, Any], model_tier: str) -> dict[str, Any]:
        """Invoke Layer 2 builder agent and apply deterministic Python AST / doc tools."""
        registry = read_json_state(self.registry_path).get("agents", {})
        agent_id = self._resolve_active_agent(task.get("assigned_agent"), fallback="seed_coder")
        task["assigned_agent"] = agent_id

        agent_meta = registry.get(agent_id, {})
        agent_md = self.adk_root / agent_meta.get("path", f"agents/building/{agent_id}.md")
        if not agent_md.exists():
            agent_md = self.adk_root / "agents" / "building" / "seed_coder.md"

        node_id, node_path = self._resolve_target_node(task.get("target_node") or THESIS_FILE, task=task, fallback=THESIS_FILE)
        task["target_node"] = node_id
        full_target = self.workspace_dir / node_path
        existing_content = full_target.read_text(encoding="utf-8") if full_target.exists() else ""

        # A long document goes in as its outline plus the part the task works on, never as a whole.
        if node_path.endswith((".md", ".tex")) and len(existing_content) > 1500:
            payload_existing_content = _document_context(existing_content, str(task.get("description", "")))
        else:
            payload_existing_content = existing_content

        self.logger.log_step(
            "BUILDING",
            f"Zadanie {task.get('task_id')} -> agent '{agent_id}' na wierzchołku {node_id} ({node_path})",
            {"model_tier": model_tier, "include_docs": self.include_docs},
        )
        # The task's content and the slice of H its vertex determines; nothing else about the project (Audit VIII §X).
        builder_payload: dict[str, Any] = {
            "user_prompt": self.current_user_prompt,
            "task": task,
            "target_file": node_path,
            "existing_content": payload_existing_content,
            # One source of truth for external imports (D2): the canonical import line of every package this
            # fixed environment provides. Anything else is unavailable for the whole run (D1).
            "available_packages": available_package_imports(),
            **self._context_for(self._task_vertex(task), node_path),
        }
        done_when = self._done_when(node_path, builder_payload)
        if done_when:
            builder_payload["done_when"] = done_when
        # A repair sees the tests it has to satisfy, not only a prose summary of their failure.
        is_doc_or_research_agent = _is_document(node_path) or agent_id in (
            "seed_writer", "background_researcher", "discoverer_researcher", "sota_researcher"
        )
        if task.get("repair_of") and not is_doc_or_research_agent:
            failing = self._failing_test_sources()
            if failing:
                builder_payload["failing_tests"] = failing

        writer = {"agent": agent_id, "task_id": str(task.get("task_id", ""))}
        llm_res = self._call_agent(agent_md, builder_payload, model_tier=model_tier, provider=self.provider)
        try:
            self._materialize_workspace_artifact(node_path, llm_res.get("output", {}), writer=writer)
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
            # The vertex remembers the rejection like a failed verification: the next attempt, the model choice
            # and the re-plan's dossier all see it (§XI B4, A).
            h = self._project_h()
            self._remember_verdict(h.owner_of(node_path) if h is not None else None, task.get("task_id"), [f"ANSWER_REJECTED: {exc}"])
            retry_payload = {
                **builder_payload,
                "rejected_answer": {
                    "error": str(exc),
                    "instruction": texts.RETRY_INSTRUCTION,
                },
            }
            llm_res = self._call_agent(agent_md, retry_payload, model_tier=model_tier, provider=self.provider)
            self._materialize_workspace_artifact(node_path, llm_res.get("output", {}), writer=writer)
        return llm_res

    def _done_when(self, node_path: str, payload: dict[str, Any]) -> list[str]:
        """What the verification of this task will check, stated up front (U6, 2026-11-15: a task was prose only;
        the agent learned what counts as done from its first failure). The tests of a module come from its I bag."""
        if node_path.endswith(".py"):
            name = Path(node_path).name
            if name.startswith("test_") or name.endswith("_test.py"):
                return texts.done_when_test(node_path)
            return texts.done_when_module(node_path, list(payload.get("tested_by") or []))
        if _is_document(node_path):
            return texts.done_when_document(bool((payload.get("may_cite") or {}).get("available_csv_rows")))
        return []

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

    def _experiment_still_stubbed(self) -> bool:
        """A module the experiment runs (a code member of R in H) is still a stub: running it can only raise
        NotImplementedError (mock 01, 2026-11-18: DATA_FAILED after config.py while core.py was a stub)."""
        from adk.hypergraph.oracles import is_stub

        h = self._project_h()
        run = h.edges.get("R:run") if h is not None else None
        if run is None:
            return False
        for member, role in run.members.items():
            path = self.workspace_dir / member
            if role not in ("P", "C") or not member.endswith(".py") or not path.is_file():
                continue
            try:
                if is_stub(path.read_text(encoding="utf-8", errors="replace")):
                    return True
            except (SyntaxError, ValueError):
                continue  # an unparsable module is the syntax guard's finding; the run shows the real error
        return False

    def _refresh_experiment_after_code(self, node_id: str) -> None:
        """After any change to Python code, results are whatever the declared entrypoint just wrote."""
        node_path = str(node_id).partition("#")[0]
        if not node_path.endswith(".py"):
            return
        if self._experiment_still_stubbed():
            self._last_experiment_error = ""
            return
        from adk.tools.building.experiment_runner import execute_workspace_experiment

        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        entrypoint = str(blueprint.get("entrypoint") or "").strip() if isinstance(blueprint, dict) else ""
        result = execute_workspace_experiment(self.workspace_dir, entrypoint=entrypoint or None)
        if result.get("skipped") or result.get("ok"):
            self._last_experiment_error = ""
            if result.get("ok"):
                self._record_data_produced()
            return
        self._last_experiment_error = str(result.get("error") or texts.EXPERIMENT_NO_RESULTS)
        self.logger.log_event("DATA_FAILED", error=self._last_experiment_error[:400])
