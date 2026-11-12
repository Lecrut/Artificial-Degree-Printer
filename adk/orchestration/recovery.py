"""Recovery: queues rebuilt from the factual audit, and delivery with listed gaps."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any

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
                        "description": f"Napraw plik {rel}. Błędy: {'; '.join(errs)}",
                        "target_node": rel,
                        "assigned_agent": _agent_for_path(rel),
                        "status": "TODO",
                    }
                )
            if unlocated or not by_file:
                detail = "; ".join(unlocated) or "pytest nie przechodzi"
                tasks.append(
                    {
                        "task_id": f"{prefix}_CODE",
                        "description": f"Napraw kod tak, żeby testy przeszły. Błędy bez wskazanego pliku: {detail}",
                        "target_node": self._role_file("core"),
                        "assigned_agent": "seed_coder",
                        "status": "TODO",
                    }
                )
        elif not audit.get("csv_columns"):
            # Results are produced by running the experiment; a missing file is a defect of the producing code.
            tasks.append(
                {
                    "task_id": f"{prefix}_RESULTS",
                    "description": "Eksperyment nie wyprodukował pliku wyników. Popraw kod tak, żeby punkt wejścia eksperymentu zapisywał wyniki.",
                    "target_node": self._role_file("core"),
                    "assigned_agent": "seed_coder",
                    "status": "TODO",
                }
            )
        for number in audit.get("chapters_missing") or []:
            tasks.append(
                {
                    "task_id": f"{prefix}_CH{number}",
                    "description": f"Napisz Rozdział {number} w thesis.md. Zastąp sekcję, nie doklejaj drugiej kopii.",
                    "target_node": THESIS_FILE,
                    "assigned_agent": "seed_writer",
                    "status": "TODO",
                }
            )
        # Every critic finding becomes work: findings that name a workspace file go to that file, the rest
        # (claims, numbers, contradictions in the text) go to the writer, each with its own id. Findings that
        # still stand when the budget runs out are listed as gaps (see _finalize_with_gaps), never dropped.
        handled = {err for errs in by_file.values() for err in errs}
        known_files = [
            str(m.get("path", ""))
            for m in read_json_state(self.matrix_path).get("nodes", {}).values()
            if str(m.get("path", "")).endswith(".py")
        ]
        content_findings: list[str] = []
        for issue in audit.get("trigger_issues") or []:
            text = str(issue)
            if text in handled or any(tok in text.lower() for tok in ("tectonic", "latex", "kompilacja pdf")):
                continue
            named = [p for p in known_files if re.search(rf"(?<![\w/]){re.escape(Path(p).name)}\b", text)]
            if named:
                target = self._repair_target(named[0])
                tasks.append(
                    {
                        "task_id": f"{prefix}_FIX_{Path(target).stem}_{len(tasks) + 1}",
                        "description": f"Napraw plik {target} zgodnie z ustaleniem weryfikacji: {text}",
                        "target_node": target,
                        "assigned_agent": _agent_for_path(target),
                        "status": "TODO",
                    }
                )
            else:
                content_findings.append(text)
        if content_findings:
            numbered = "\n".join(f"[K{i}] {finding}" for i, finding in enumerate(content_findings, 1))
            tasks.append(
                {
                    "task_id": f"{prefix}_CRITIC",
                    "description": (
                        "Popraw thesis.md tak, by usunąć każde z ustaleń krytyka. Odnieś się do każdego identyfikatora; "
                        f"jeśli ustalenia nie da się usunąć, opisz je wprost jako ograniczenie pracy.\n{numbered}"
                    ),
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
                    "description": (
                        "Kompilacja thesis.pdf nie przeszła. Popraw thesis.md i kod tak, "
                        f"żeby LaTeX się zbudował. Log: {_clip_log(trigger_text)}"
                    ),
                    "target_node": THESIS_FILE,
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
                    "target_node": THESIS_FILE,
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
            if isinstance(task, dict) and task.get("status") in ("FAILED", "BLOCKED"):
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
            f"  [NOWA KOLEJKA {generation + 1}/3] {len(tasks)} zadań z audytu, stara kolejka przerwana.",
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
        state.tasks = rebuilt["tasks"]
        state.generation += 1
        return None
