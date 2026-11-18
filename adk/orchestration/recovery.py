"""Recovery: queues rebuilt from the factual audit, and delivery with listed gaps."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state, write_json_state
from adk.tools.building import (
    edit_document_section,
)
from adk.orchestration.common import (
    _issue_signature,
    GAPS_SECTION_TITLE,
    _clip_log,
    _plain_text,
    THESIS_FILE,
    _RunState,
    _agent_for_path,
)


_POINTER_FINDING = re.compile(
    r"\\ref_|pointer|symbolic tag|^(?:Symbol|Row selector|Column|Figure reference|Citation key) '[^']*' not found in", re.I
)


def _is_pointer_finding(text: str) -> bool:
    """A finding of the pointer compiler (`ref_compiler`): it concerns the thesis, whatever file it names."""
    return bool(_POINTER_FINDING.search(text.strip()))


class RecoveryMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _tasks_from_audit(self, audit: dict[str, Any], generation: int) -> list[dict[str, Any]]:
        """Turn the factual audit into the only tasks still worth doing."""
        prefix = f"Q{generation}"
        tasks: list[dict[str, Any]] = []
        by_file: dict[str, list[str]] = {}
        if audit.get("pytest_status") != "PASS" or audit.get("pytest_errors"):
            py_errs = audit.get("pytest_errors") or []
            # One task per file named in the diagnostics: the repair goes to the file that failed, not to a file
            # guessed from a substring of the message.
            unlocated: list[str] = []
            for err in py_errs:
                paths = self._workspace_paths_in(err)
                for rel in paths:
                    by_file.setdefault(self._repair_target(rel), []).append(err)
                if not paths:
                    unlocated.append(err)
            for idx, (rel, errs) in enumerate(by_file.items(), 1):
                tasks.append(
                    {
                        "task_id": f"{prefix}_FIX{idx}",
                        "description": texts.fix_file_task(rel, errs),
                        "target_node": rel,
                        "assigned_agent": _agent_for_path(rel),
                        "status": "TODO",
                    }
                )
            if unlocated or not by_file:
                detail = "; ".join(unlocated) or texts.PYTEST_FAILS
                tasks.append(
                    {
                        "task_id": f"{prefix}_CODE",
                        "description": texts.fix_code_task(detail),
                        "target_node": self._entry_file() or THESIS_FILE,
                        "assigned_agent": "seed_coder",
                        "status": "TODO",
                    }
                )
        elif not audit.get("csv_columns"):
            # Results are produced by running the experiment; a missing file is a defect of the producing code.
            tasks.append(
                {
                    "task_id": f"{prefix}_RESULTS",
                    "description": texts.RESULTS_TASK,
                    "target_node": self._entry_file() or THESIS_FILE,
                    "assigned_agent": "seed_coder",
                    "status": "TODO",
                }
            )
        for number in audit.get("chapters_missing") or []:
            tasks.append(
                {
                    "task_id": f"{prefix}_CH{number}",
                    "description": texts.write_chapter_task(number),
                    "target_node": THESIS_FILE,
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        # Every critic finding becomes work: findings that name a workspace file go to that file, the rest
        # (claims, numbers, contradictions in the text) go to the writer, each with its own id. Findings that
        # still stand when the budget runs out are listed as gaps (see _finalize_with_gaps), never dropped.
        handled = {err for errs in by_file.values() for err in errs}
        # While the code fails or has written no results, a pointer to results cannot resolve whatever the writer
        # does: such findings wait for green code and stay listed as gaps meanwhile (U9, 2026-11-15: every
        # generation Q1-Q4 gave the writer CRITIC + REFS on \ref_csv while results.csv did not exist).
        code_red = audit.get("pytest_status") != "PASS" or bool(audit.get("pytest_errors")) or not audit.get("csv_columns")

        def _waits_for_results(text: str) -> bool:
            return code_red and ("ref_csv" in text or "csv" in text.lower())

        h = self._project_h()
        known_files = sorted({f for v in (h.vertices if h else {}) for f in h.files_of(v) if f.endswith(".py")})
        content_findings: list[str] = []
        for issue in audit.get("trigger_issues") or []:
            text = str(issue)
            if text in handled or _waits_for_results(text) or any(tok in text.lower() for tok in ("tectonic", "latex", "kompilacja pdf", texts.PDF_FAILED.lower())):
                continue
            named = [p for p in known_files if re.search(rf"(?<![\w/]){re.escape(Path(p).name)}\b", text)]
            # A finding about a pointer in the thesis names the code file the pointer aims at, but the pointer is
            # the writer's (N bag): on 2026-11-16 "Symbol 'CONFIG' not found in 'config.py'" went to the coder (X6).
            if named and not _is_pointer_finding(text):
                target = self._repair_target(named[0])
                tasks.append(
                    {
                        "task_id": f"{prefix}_FIX_{Path(target).stem}_{len(tasks) + 1}",
                        "description": texts.fix_finding_task(target, text),
                        "target_node": target,
                        "assigned_agent": _agent_for_path(target),
                        "status": "TODO",
                    }
                )
            else:
                content_findings.append(text)
        # Broken pointers and critic findings on the same thesis are one task, not two (REFS was always BLOCKED
        # behind a failed CRITIC on the same file).
        content_findings += [
            str(err) for err in audit.get("symbolic_errors") or [] if not _waits_for_results(str(err)) and str(err) not in content_findings
        ]
        if content_findings:
            numbered = "\n".join(f"[K{i}] {finding}" for i, finding in enumerate(content_findings, 1))
            tasks.append(
                {
                    "task_id": f"{prefix}_CRITIC",
                    "description": texts.critic_task(numbered),
                    "target_node": THESIS_FILE,
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )

        trigger_text = " ".join(str(item) for item in (audit.get("trigger_issues") or [])).lower()
        if any(token in trigger_text for token in ("pdf", "tectonic", "latex")):
            tasks.append(
                {
                    "task_id": f"{prefix}_PDF",
                    "description": texts.pdf_task(_clip_log(trigger_text)),
                    "target_node": THESIS_FILE,
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        if not tasks:
            detail = "; ".join(audit.get("trigger_issues") or []) or texts.FINAL_GATE_FAILED
            tasks.append(
                {
                    "task_id": f"{prefix}_CLOSE",
                    "description": texts.close_task(detail),
                    "target_node": THESIS_FILE,
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        return tasks

    def _finalize_with_gaps(self, audit: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
        """Close an exhausted run: list every unresolved finding, write it into the thesis, try to build the PDF.

        The gap section is generated from data, not by a model, so it cannot hide or soften what is missing.
        """
        gaps: list[dict[str, str]] = []
        seen: set[str] = set()

        def _add(kind: str, detail: str) -> None:
            text = str(detail).strip()
            if text and text not in seen:
                seen.add(text)
                gaps.append({"kind": kind, "detail": text})

        for err in audit.get("pytest_errors") or []:
            _add("kod", err)
        for number in audit.get("chapters_missing") or []:
            _add("rozdział", f"Brak rozdziału {number}.")
        for err in audit.get("symbolic_errors") or []:
            _add("wskaźnik", err)
        for issue in audit.get("trigger_issues") or []:
            _add("ustalenie weryfikacji", issue)
        queue = read_json_state(self.task_queue_path) if self.task_queue_path.exists() else []
        for task in queue if isinstance(queue, list) else []:
            if isinstance(task, dict) and task.get("status") == "FAILED":
                _add("zadanie", f"{task.get('task_id')} ({task.get('status')}): {task.get('description', '')}")
            if isinstance(task, dict) and task.get("harness_bug"):
                bug = task["harness_bug"]
                _add("błąd harnessu", f"{task.get('task_id')}: {bug.get('reason', '')} Pliki: {bug.get('files_in_error') or bug.get('file')}")

        thesis_md = self.workspace_dir / "thesis.md"
        if self.include_docs and thesis_md.exists() and gaps:
            lines = [
                "Poniższa lista została wygenerowana automatycznie z raportu weryfikacji, a nie przez model językowy. "
                "Wymienia ustalenia, których nie udało się usunąć w budżecie napraw.",
                "",
            ]
            lines += [f"{i}. [{g['kind']}] {_plain_text(g['detail'])}" for i, g in enumerate(gaps, 1)]
            edit_document_section(thesis_md, GAPS_SECTION_TITLE, "\n".join(lines))

        pdf_failure = self._pdf_failure_report()
        if pdf_failure is not None:
            _add("pdf", "; ".join(pdf_failure.get("issues") or ["Kompilacja PDF nie powiodła się."]))

        closed = dict(report)
        closed["gaps"] = gaps
        closed["summary"] = f"Zakończono z brakami: {len(gaps)} nierozwiązanych ustaleń."
        write_json_state(self.validation_report_path, closed)
        print(f"  [KONIEC Z BRAKAMI] {len(gaps)} nierozwiązanych ustaleń zapisano w pracy i w raporcie.", flush=True)
        return {"gaps": gaps, "pdf_ok": pdf_failure is None}

    def _rebuild_queue(self, report: dict[str, Any], generation: int, seen_signatures: list[str]) -> dict[str, Any]:
        """After 3 failed repairs, drop the old queue and return a new one, or a terminal payload.

        `seen_signatures` holds every audit signature of this run (appended here), so an A -> B -> A
        oscillation is recognised as a repeat, not only an immediate A -> A.
        """
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
        repeated = signature in seen_signatures
        seen_signatures.append(signature)
        if (repeated and generation >= 2) or generation >= 4:
            if repeated:
                reason = "AUDYT PLIKOW SIE NIE ZMIENIL PO WIELOKROTNYCH PROBACH."
            else:
                reason = "WYCZERPANO CZTERY PRZEBUDOWY KOLEJKI."
            # Exhaustion delivers the work with its gaps listed, instead of pausing with no artifact at all.
            self._shout_problem_stop(f"{reason} KONCZE PRACE Z JAWNA LISTA BRAKOW.")
            closing = self._finalize_with_gaps(audit, report)
            return {
                "stop": {
                    "status": "COMPLETED_WITH_GAPS",
                    "reason": "QUEUE_REBUILD_EXHAUSTED",
                    "audit": audit,
                    "gaps": closing["gaps"],
                    "pdf_ok": closing["pdf_ok"],
                }
            }
        tasks = self._tasks_from_audit(audit, generation + 1)
        write_json_state(self.task_queue_path, tasks)
        print(
            f"  [NOWA KOLEJKA {generation + 1}/4] {len(tasks)} zadań z audytu, stara kolejka przerwana.",
            flush=True,
        )
        self._record_evolution_event(
            {"type": "QUEUE_REBUILT", "generation": generation + 1, "task_ids": [t["task_id"] for t in tasks]}
        )
        return {"tasks": tasks, "signature": signature}

    def _next_generation(self, state: _RunState, report: dict[str, Any]) -> dict[str, Any] | None:
        """Replace the queue with one built from the factual audit; the terminal payload when the budget is spent."""
        rebuilt = self._rebuild_queue(report, state.generation, state.seen_audit)
        if "stop" in rebuilt:
            stop = rebuilt["stop"]
            stop.update(state.outcome(validation_report={**report, "gaps": stop.get("gaps", [])}))
            return stop
        state.tasks = rebuilt["tasks"] + self._carry_over(state.tasks)
        state.generation += 1
        return None
