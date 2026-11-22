"""What kind of failure a verification report is: stable fingerprints of its findings (to tell a repeated failure
from a new one) and its category (what evolution may learn from). Split from `common` on 2026-11-21."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts


_RUFF_FINDING = re.compile(r"\b([A-Z]{1,4}\d{3,4})\b[^\n]*\n\s*-->\s*(.+?):\d+:\d+")
# ruff's concise format `src\experiment_runner.py:35:20: F821 ...` (2026-11-20: unmatched, F821 fell into `generic`)
_RUFF_CONCISE = re.compile(r"(\S+?\.py):\d+:\d+: ([A-Z]{1,4}\d{3,4})\b")
# The exception of a Python traceback (a run of the experiment or of the plots function): its last `XError:` line.
_TRACEBACK_EXC = re.compile(r"^([A-Za-z_]\w*(?:Error|Exception)):", re.MULTILINE)
_PYTEST_FINDING = re.compile(r"(?:FAILED|ERROR)\s+(\S+?\.py)(?:::(\S+))?(?:\s+-\s+(\w+))?")
_FILE_FINDING = re.compile(r"\b(Syntax|Import) error in (\S+?\.py)")
# pytest `E   ValueError: ...` / `E   Failed: DID NOT RAISE` — the full exception name of a failed test
_PYTEST_E_LINE = re.compile(r"^E\s+([A-Za-z_]\w*(?:Error|Exception|Exit|Failed|Interrupt))\b", re.MULTILINE)


def _issue_fingerprints(issue: str) -> list[str]:
    """Identity of one finding as `file:rule`, independent of identifiers, line numbers and wording.

    Renaming an unused variable (`width` -> `bars` -> `plot_df`) changes the diagnostic text but not the defect,
    so the raw text cannot tell a repeated failure from a new one.
    """
    found = [f"{Path(path.replace(chr(92), '/')).name}:{code}" for code, path in _RUFF_FINDING.findall(issue)]
    found += [f"{Path(path.replace(chr(92), '/')).name}:{code}" for path, code in _RUFF_CONCISE.findall(issue)]
    found += [
        f"{Path(path).name}::{test or '*'}:{exc or 'fail'}" for path, test, exc in _PYTEST_FINDING.findall(issue)
    ]
    found += [f"{path}:{kind}Error" for kind, path in _FILE_FINDING.findall(issue)]
    if found:
        return found
    # No recognisable diagnostic: mask numbers and quoted/backticked names, keep the wording.
    masked = re.sub(r"`[^`]*`|'[^']*'|\"[^\"]*\"", "<id>", issue)
    return [re.sub(r"\d+", "#", masked).strip()[:200]]


# A builder answer the write gate refused (or a builder exception). The gate already returned the exact reason
# to the agent and retried it; a prompt rule cannot add to that, so such failures never feed evolution.
# All three exception wrappers count: task, fast repair and repair task (agent_texts.*_exception)
# (the last two used to fall into `generic`: 15/26 failures of the 2026-11-14 run).
_GATE_REJECTION = texts.GATE_REJECTION


_SPEC_FINDING = re.compile(
    r"(?:API_\w+|IMPORT_OUTSIDE_SPEC|IMPORT_NOT_IN_PLAN|FILE_OUTSIDE_PLAN|TEST_OUTSIDE_SPEC|TEST_INVALID_ON_STUBS)\b"
    r"|Write rejected: the answer breaks the specification"
)


def _issue_category(issues: list[Any]) -> str:
    """Kind of a failure, independent of the file: a ruff code (`F821`), `pytest:<Exception>`, `SyntaxError`,
    `ImportError`, `contract` (a verified finding: a test or module uses a name its neighbour does not define),
    `harness` (an answer refused by the write gate / a builder exception), `document` (unresolved thesis
    pointers), `run:<Exception>` (a traceback of the
    experiment), or `generic` (unrecognised; never a pattern for
    evolution: on 2026-11-20 it joined a wrong plan example and a missing import into one "pattern"). Evolution reacts to a category repeating across tasks, not to one incident.

    A gate rejection outweighs whatever it quotes: its text carries the inner error ("SyntaxError", pytest lines)
    of an answer that never reached the disk, so that error is not what the workspace failed on."""
    counts: Counter[str] = Counter()
    for item in issues:
        text = str(item)
        if _SPEC_FINDING.match(text.strip()):
            counts["spec"] += 1  # a breach of σ: enforced by the harness, never a prompt rule (Audit VI A10)
            continue
        if _GATE_REJECTION.search(text):
            counts["harness"] += 1
            continue
        counts.update(code for code, _ in _RUFF_FINDING.findall(text))
        counts.update(code for _, code in _RUFF_CONCISE.findall(text))
        if "Traceback (most recent call last)" in text and (exc := _TRACEBACK_EXC.findall(text)):
            counts[f"run:{exc[-1]}"] += 1
        # The exception name from pytest's `E   XError: ...` lines is never truncated; the short-summary name is a
        # fallback only (it was cut to "AssertionEr..." in a narrow terminal, N4).
        e_names = set(_PYTEST_E_LINE.findall(text))
        if e_names:
            counts.update(f"pytest:{name}" for name in e_names)
        else:
            counts.update(f"pytest:{exc or 'fail'}" for _, _, exc in _PYTEST_FINDING.findall(text))
        counts.update(f"{kind}Error" for kind, _ in _FILE_FINDING.findall(text))
        lowered = text.lower()
        if "contract violation" in lowered:
            counts["contract"] += 1
        elif "does not parse" in lowered or "syntaxerror" in lowered or "invalid-syntax" in lowered:
            counts["SyntaxError"] += 1
        elif "pointer" in lowered or "symbolic tag" in lowered or "does not exist" in lowered:
            counts["document"] += 1
    return counts.most_common(1)[0][0] if counts else UNCLASSIFIED_CATEGORY


# Categories the harness itself enforces (syntax guard, import resolution, answer shape): a prompt rule cannot
# add anything, so they never trigger evolution (Audit IV §IV.6.3 B2).
HARNESS_ENFORCED_CATEGORIES = {"SyntaxError", "invalid-syntax", "E999", "ImportError", "harness", "spec"}
UNCLASSIFIED_CATEGORY = "generic"

def _issue_signature(report: dict[str, Any]) -> str:
    """Stable identity of a verification failure: the sorted set of `file:rule` fingerprints of its issues."""
    issues = report.get("issues") or []
    if not isinstance(issues, list):
        issues = [issues]
    prints: set[str] = set()
    for item in issues:
        text = str(item).strip()
        if text:
            prints.update(_issue_fingerprints(text))
    return "\n".join(sorted(prints))


def _collect_report_issues(report: dict[str, Any]) -> list[str]:
    """All issues of a verification report: builder exceptions (top-level `issues`) plus every supervisor's
    `issues`. ValidationReport keeps pytest/ruff/ref errors under `supervisors.*.issues`, not at top level."""
    raw = report.get("issues") or []
    items = list(raw) if isinstance(raw, list) else [raw]
    for supervisor in (report.get("supervisors") or {}).values():
        if isinstance(supervisor, dict):
            items.extend(supervisor.get("issues") or [])
    return list(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))
