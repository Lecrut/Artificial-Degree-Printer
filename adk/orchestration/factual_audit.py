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
from adk.orchestration.common import (
    _collect_report_issues,
    _fit_items,
)


_CHAPTER_HEADING_WORDS = {
    1: ("wstęp", "wstep", "cel", "teza", "intro", "problem"),
    2: ("sota", "stan wiedzy", "literatur", "przegląd", "przeglad", "related", "background"),
    3: ("architektur", "formalizm", "matematyczn", "system", "design", "model"),
    4: ("implementacj", "algorytm", "struktury", "implementation"),
    5: ("wyniki", "ewaluacj", "eksperyment", "badani", "evaluation", "metodologia", "empirical", "results"),
    6: ("podsumowan", "wnioski", "conclusi", "kierunki", "summary"),
}


def thesis_missing_chapters(thesis_text: str, expected: list[int] | range = range(1, 7)) -> list[int]:
    """Expected chapters with no `## ` heading in the thesis: a heading counts by its number
    (`Rozdział 3`, `Chapter 3`) or, without one, by the first chapter whose words it contains."""
    found: set[int] = set()
    for match in re.finditer(r"^##\s+([^\n]+)", thesis_text, flags=re.MULTILINE):
        heading = match.group(1).lower()
        number = re.search(r"(?:rozdzia[łl]|chapter)\s+(\d+)", heading)
        if number:
            found.add(int(number.group(1)))
            continue
        hit = next((n for n, words in _CHAPTER_HEADING_WORDS.items() if any(w in heading for w in words)), None)
        if hit is not None:
            found.add(hit)
    return [n for n in expected if n not in found]


class FactualAuditMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _expected_chapters(self) -> list[int]:
        """The chapters this thesis must have: the plan's (`planned_chapters`, the N bags of H). The canonical six
        remain only for a run without a planned outline (2026-11-17: 5 planned chapters, the final gate demanded a
        sixth, and `Q1_CH6` wrote a chapter outside the plan)."""
        planned = (read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}).get("planned_chapters")
        indices = sorted({
            int(ch["index"]) for ch in planned or []
            if isinstance(ch, dict) and str(ch.get("index", "")).isdigit()
        })
        return indices or list(range(1, 7))

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
                    pending.update({m for m, role in run.members.items() if role == "O"} | {"figures", "plot_results.py"})
        return pending

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
        expected = self._expected_chapters()
        thesis = self.workspace_dir / "thesis.md"
        if thesis.exists():
            for match in re.finditer(r"^##\s+.*?(\d+)", thesis.read_text(encoding="utf-8"), flags=re.MULTILINE):
                number = int(match.group(1))
                if number in expected and number not in chapters_present:
                    chapters_present.append(number)
        chapters_missing = [n for n in expected if n not in chapters_present] if self.include_docs else []

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
