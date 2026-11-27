"""Milestone checks of the whole workspace: the factual audit behind queue rebuilds, the PDF build, files still to come."""

from __future__ import annotations


import os
import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state, write_json_state
from adk.tools.verification import (
    compile_symbolic_references,
    run_isolated_tests,
)
from adk.orchestration.common import _fit_items
from adk.orchestration.failure_kinds import _collect_report_issues


_ROMAN = {"i": 1, "v": 5, "x": 10}


def _chapter_number(heading: str) -> int | None:
    """The number in `Rozdział 3`, `Chapter 3` or `Rozdział III` (the writer numbers in both ways); None without one."""
    found = re.search(r"(?:rozdzia[łl]|chapter)\s+(\d+|[ivx]+)\b", heading.lower())
    if not found:
        return None
    token = found.group(1)
    if token.isdigit():
        return int(token)
    values = [_ROMAN[c] for c in token]
    return sum(-v if i + 1 < len(values) and v < values[i + 1] else v for i, v in enumerate(values))


def thesis_missing_chapters(thesis_text: str, expected: dict[int, str]) -> list[int]:
    """Planned chapters (number -> title) with no `## ` heading in the thesis: a heading counts by its number
    (`Rozdział 3`, `Chapter 3`) or, without one, by the planned title it contains."""
    found: set[int] = set()
    for match in re.finditer(r"^##\s+([^\n]+)", thesis_text, flags=re.MULTILINE):
        heading = match.group(1).lower()
        number = _chapter_number(heading)
        if number is not None:
            found.add(number)
            continue
        hit = next((n for n, title in expected.items() if title and title.lower()[:18] in heading), None)
        if hit is not None:
            found.add(hit)
    return [n for n in expected if n not in found]


class FactualAuditMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _expected_chapters(self) -> dict[int, str]:
        """The chapters this thesis must have (number -> title): only the plan's `planned_chapters` — no canonical
        six (2026-11-17: 5 planned chapters, the final gate demanded a sixth; §XIII F6)."""
        return self._planned_chapter_titles()

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
        h = self._project_h()
        run = h.edges.get("R:run") if h is not None else None

        for t in tasks:
            if not isinstance(t, dict):
                continue
            t_id = str(t.get("task_id", ""))
            if t_id == current_id:
                found_current = True
                continue
            if found_current and t.get("status") in ("TODO", "WAITING"):
                path_str = str(t.get("target_node", "")).partition("#")[0]
                if path_str:
                    pending.add(Path(path_str).name)
                    pending.add(path_str)
                # Code the experiment still has to run: its results and figures are pending too (from R in H).
                if run is not None and run.members.get(path_str) in ("P", "C"):
                    plots_file = str(run.spec.get("plots") or "").partition(":")[0]
                    pending.update({m for m, role in run.members.items() if role == "O"} | {"figures"} | ({plots_file} - {""}))
        return pending

    def _audit_factual_state(self, report: dict[str, Any]) -> dict[str, Any]:
        """Read the workspace as it is. The next queue is built from this, not from the abandoned plan."""
        test_res = run_isolated_tests(
            self.workspace_dir,
            verification_dir=self.adk_root / "tools" / "verification",
        )
        files: list[str] = []
        if self.workspace_dir.exists():
            for path in sorted(self.workspace_dir.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and ".compiled." not in path.name:
                    files.append(path.relative_to(self.workspace_dir).as_posix())

        expected = self._expected_chapters()
        thesis = self.workspace_dir / "thesis.md"
        thesis_text = thesis.read_text(encoding="utf-8") if thesis.exists() else ""
        chapters_missing = thesis_missing_chapters(thesis_text, expected) if self.include_docs else []

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
            "chapters_present": [n for n in expected if n not in chapters_missing],
            "chapters_missing": chapters_missing,
            "symbolic_errors": symbolic_errors,
            "csv_columns": csv_columns,
            "trigger_issues": [str(item) for item in trigger_issues],
        }
        write_json_state(self.state_dir / "factual_audit.json", audit)
        return audit

    def _pdf_failure_report(self) -> dict[str, Any] | None:
        """Compile the thesis. A failure comes back as a queue-rebuild reason. `HARNESS_SKIP_PDF=1` (the test suite)
        skips the LaTeX build; which agents answered — a model or a simulation — never changes this path."""
        if os.environ.get("HARNESS_SKIP_PDF") == "1":
            return None
        thesis_md = self.workspace_dir / "thesis.md"
        if not thesis_md.exists():
            return {"status": "FAIL", "issues": [texts.NO_THESIS_FOR_PDF]}
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
                abstract=str(blueprint.get("thesis_statement") or ""),
            )
            pdf_path = self.workspace_dir / "thesis.pdf"
            compiled = compile_latex_to_pdf(tex_path, pdf_path)
        except Exception as exc:
            return {"status": "FAIL", "issues": [f"{texts.PDF_FAILED}: {exc}"]}
        if compiled and pdf_path.exists() and pdf_path.read_bytes()[:5] == b"%PDF-":
            return None
        log_path = self.workspace_dir / "logs" / "tectonic.log"
        log_text = (
            log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            if log_path.exists()
            else texts.NO_TECTONIC_LOG
        )
        return {"status": "FAIL", "issues": [f"{texts.PDF_FAILED}.\n{log_text}"]}
