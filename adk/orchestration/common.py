"""Module-level helpers and constants shared by the orchestrator and its mixins."""

from __future__ import annotations


import csv
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any
from adk.orchestration import agent_texts as texts
from adk.orchestration import agent_task_templates as templates


def _filter_bibtex(bib_text: str, allowed_keys: set[str]) -> tuple[str, list[str]]:
    """Keep only entries whose citation key is in `allowed_keys`; return the kept text and the dropped keys."""
    entry_pattern = re.compile(r"(@\w+\s*\{\s*([^,\s]+)\s*,.*?\n\})", re.DOTALL)
    kept: list[str] = []
    dropped: list[str] = []
    for match in entry_pattern.finditer(bib_text):
        key = match.group(2).strip()
        if key in allowed_keys:
            kept.append(match.group(1).strip())
        else:
            dropped.append(key)
    return "\n\n".join(kept), dropped


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


_RUFF_FINDING = re.compile(r"\b([A-Z]{1,4}\d{3,4})\b[^\n]*\n\s*-->\s*(.+?):\d+:\d+")
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


def _issue_category(issues: list[Any]) -> str:
    """Kind of a failure, independent of the file: a ruff code (`F821`), `pytest:<Exception>`, `SyntaxError`,
    `ImportError`, `contract` (a verified finding: a test or module uses a name its neighbour does not define),
    `harness` (an answer refused by the write gate / a builder exception), `document` (unresolved thesis
    pointers), or `generic`. Evolution reacts to a category repeating across tasks, not to one incident.

    A gate rejection outweighs whatever it quotes: its text carries the inner error ("SyntaxError", pytest lines)
    of an answer that never reached the disk, so that error is not what the workspace failed on."""
    counts: Counter[str] = Counter()
    for item in issues:
        text = str(item)
        if _GATE_REJECTION.search(text):
            counts["harness"] += 1
            continue
        counts.update(code for code, _ in _RUFF_FINDING.findall(text))
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
    return counts.most_common(1)[0][0] if counts else "generic"


# Categories the harness itself enforces (syntax guard, import resolution, answer shape): a prompt rule cannot
# add anything, so they never trigger evolution (Audit IV §IV.6.3 B2).
HARNESS_ENFORCED_CATEGORIES = {"SyntaxError", "invalid-syntax", "E999", "ImportError", "harness"}
# Repairs sent straight back to the failed file's author with the verification findings, before the one
# planner-and-evolution cycle a task gets (Audit IV §IV.7 pkt 6).
FAST_REPAIR_ATTEMPTS = 2


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


def _looks_like_workspace_path(value: str) -> bool:
    """A relative file path with an extension, inside the workspace (no absolute paths, no '..')."""
    p = Path(value.strip().replace("\\", "/")) if value else None
    return bool(p and p.suffix and not p.is_absolute() and ".." not in p.parts and " " not in value.strip())


GAPS_SECTION_TITLE = "Braki i ograniczenia realizacji"

# INSTALL_DEPENDENCY / INSTALL_PACKAGE removed 2026-11-14 (D1): the environment is fixed for the whole run.
_KNOWN_EVOLUTION_ACTIONS = {
    "HITL", "CREATE_AGENT", "SPLIT_AGENT", "CREATE_TOOL", "MUTATE_AGENT",
    "REPORT_HARNESS_BUG",
}

# The canonical import of every package generated code may use (alias, module probed, the one true import line).
# One source of truth for external imports (D2): the model never guesses, the harness never sprays imports.
_CANONICAL_PACKAGES: tuple[tuple[str, str, str], ...] = (
    ("np", "numpy", "import numpy as np"),
    ("pd", "pandas", "import pandas as pd"),
    ("plt", "matplotlib", "import matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt"),
    ("pytest", "pytest", "import pytest"),
    ("scipy", "scipy", "import scipy"),
    ("sklearn", "sklearn", "import sklearn"),
    ("sns", "seaborn", "import seaborn as sns"),
    ("nx", "networkx", "import networkx as nx"),
)


@lru_cache(maxsize=1)
def available_package_imports() -> dict[str, str]:
    """`alias -> canonical import line` for the canonical packages actually installed in this environment."""
    import importlib.util

    out: dict[str, str] = {}
    for alias, module, line in _CANONICAL_PACKAGES:
        try:
            if importlib.util.find_spec(module) is not None:
                out[alias] = line
        except (ImportError, ValueError):
            continue
    return out
# A learned rule is permanent; one naming a task, node, queue generation or cycle describes a single incident.
_NON_GENERAL_RULE = re.compile(
    r"\b(?:T\d+(?:\.\d+)?|v\d+|Q\d+|E\d+)\b|\bzadani\w*\s+\S*\d|\btask\s+\S*\d|\bcycle\s*#?\s*\d|\bcykl\w*\s*#?\s*\d",
    re.IGNORECASE,
)

# Budgets for findings placed in a prompt, in characters (~4 characters per token). The largest prompt of the
# 2026-11-11 run was 20k tokens of a 32k context, so ~1.5k tokens of findings fit with room to spare.
FINDINGS_BUDGET_CHARS = 6000
LOG_BUDGET_CHARS = 6000


def _fit_items(items: list[str], max_chars: int = FINDINGS_BUDGET_CHARS) -> list[str]:
    """Whole findings that fit the budget, plus an explicit 'shown N of M' note. Never cuts a finding in half."""
    shown: list[str] = []
    used = 0
    for item in items:
        if shown and used + len(item) > max_chars:
            break
        shown.append(item)
        used += len(item)
    if len(shown) < len(items):
        shown.append(texts.shown_of(len(shown), len(items)))
    return shown


def _clip_log(text: str, max_chars: int = LOG_BUDGET_CHARS) -> str:
    """A log excerpt that says how much was left out instead of ending mid-line silently."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + texts.clipped(len(text) - max_chars)


def _plain_text(text: str, limit: int = 240) -> str:
    """One line of plain prose, safe for the Markdown -> LaTeX pipeline (no TeX specials, no backslash paths)."""
    first = next((line.strip() for line in str(text).splitlines() if line.strip()), "")
    cleaned = re.sub(r"[\\{}$&#^_%~`|<>]", " ", first)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1].rstrip() + "…"


def _is_document(rel_path: str) -> bool:
    return Path(str(rel_path)).suffix.lower() in (".md", ".tex", ".bib")


# The document is a format convention of the publisher, not a research decision.
THESIS_FILE = "thesis.md"
# Roles a thesis project needs. A role is played by whatever file the system created for it; the default name is
# used only while nothing exists yet. v1..v5 are accepted as input aliases (planners and fixtures emit them) and
# never stored: graph node ids are opaque.
ROLE_DEFAULTS = {
    "config": "config.py",
    "core": "core.py",
    "results": "results.csv",
    "thesis": THESIS_FILE,
    "tests": "test_core.py",
}
ROLE_ALIASES = {"v1": "config", "v2": "core", "v3": "results", "v4": "thesis", "v5": "tests"}
_CONFIG_STEMS = {"config", "settings", "params", "parameters", "hyperparameters"}


def _declared_vs_measured_metrics(declared: list[str], workspace_dir: Path) -> list[str]:
    """Compare the metrics the plan pre-registered with the `metric` column of the tidy results files.

    Deviations are allowed but must be visible: a declared metric that was never measured, or a measured one that
    was never declared, is reported (non-blocking) so the thesis has to explain it.
    """
    if not declared or not workspace_dir.exists():
        return []
    measured: set[str] = set()
    for csv_path in workspace_dir.rglob("*.csv"):
        rel = csv_path.relative_to(workspace_dir).parts
        if "logs" in rel or "benchmarks" in rel:
            continue
        try:
            with csv_path.open(encoding="utf-8", newline="") as handle:
                measured.update(str(row.get("metric", "")).strip() for row in csv.DictReader(handle) if row.get("metric"))
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    if not measured:
        return []  # nothing measured yet: the experiment has not run
    findings = [texts.metric_not_measured(m) for m in declared if m not in measured]
    findings += [texts.metric_not_declared(m) for m in sorted(measured - set(declared))]
    return findings


def _missing_chapter_tasks(issues_text: str) -> list[dict[str, Any]]:
    """Writer tasks for chapters the defense audit reported as missing."""
    match = texts.MISSING_CHAPTERS_PATTERN.search(issues_text)
    if not match:
        return []
    listed = match.group(1).lower()
    return [
        {
            "task_id": f"GATE_3_CH{number}_FIX",
            "target_node": THESIS_FILE,
            "assigned_agent": "seed_writer",
            "description": description,
            "status": "TODO",
            "covers": texts.chapter_covers(number),
        }
        for number, description in templates.CHAPTER_REPAIR.items()
        if texts.chapter_covers(number) in listed
    ]


@dataclass
class _RunState:
    """Everything one run() accumulates: the current queue and the repair bookkeeping shared by all its loops."""

    user_prompt: str
    max_retries: int
    multi_cycle_waves: bool
    tasks: list[dict[str, Any]] = field(default_factory=list)
    replan_count: int = 0
    generation: int = 0
    architecture_cycles: list[dict[str, Any]] = field(default_factory=list)
    agent_failures: dict[str, int] = field(default_factory=dict)
    seen_audit: list[str] = field(default_factory=list)
    seen_evo: set[tuple[str, str]] = field(default_factory=set)
    repeats_after_evolution: dict[tuple[str, str], int] = field(default_factory=dict)
    # (agent, failure category) -> {task_id: one clipped example}; evolution waits for a category to repeat
    # across tasks (a pattern), so the architect reasons about several incidents with different file names.
    category_hits: dict[tuple[str, str], dict[str, str]] = field(default_factory=dict)

    def outcome(self, **extra: Any) -> dict[str, Any]:
        return {"tasks": self.tasks, "replan_count": self.replan_count, "architecture_cycles": self.architecture_cycles, **extra}


def _agent_for_path(rel_path: str) -> str:
    """Default builder for a file: tests to the tester, documents to the writer, other code to the coder."""
    name = Path(rel_path).name.lower()
    if name.endswith((".md", ".tex", ".bib")):
        return "seed_writer"
    if name.startswith("test_") or name.endswith("_test.py"):
        return "seed_tester"
    return "seed_coder"


class MaterializationError(ValueError):
    """The agent returned content, but none of it was written to the workspace."""


# Every output shape a builder may use, measured on 392 real calls of the 2026-11 benchmark runs (+ `files`).
OUTPUT_SCHEMA = (
    "files[{filename, content}]",
    "ast_edits[{symbol, code, file?}]",
    "source_code (Python target only)",
    "test_code + test_file",
    "csv_content + benchmark_file",
    "plot_script + plot_file",
    "bibtex_entries + bib_file",
    "literature_review_section + section_title + research_stage",
    "section_title + section_content",
    "sections[{section_title, section_content}]",
)
# Keys that describe an answer rather than carry an artifact.
_METADATA_KEYS = {
    "summary", "status", "notes", "rationale", "research_stage", "citation_keys", "test_file", "benchmark_file",
    "plot_file", "bib_file", "section_title", "planned_visualizations", "contract_change",
    # Echo of the payload: a small model sometimes copies the task back (N7, 2026-11-15: "fields ['task']").
    "task", "target_file", "task_id",
}

SKELETON_TASK_ID = "SKELETON"


def is_skeleton_task(task: dict[str, Any] | None) -> bool:
    """The task that lays out every planned module's public interface (and its repairs, `SKELETON_FIX…`)."""
    return bool(task) and str(task.get("task_id", "")).upper().startswith(SKELETON_TASK_ID)


def build_grounded_symbols(exports_info: dict[str, Any]) -> dict[str, list[str]]:
    """Flatten hyperedge exports into the pointer targets a writer may legally cite.

    `exports` maps file -> {functions, classes, variables}; `csv_schemas` maps file -> {columns, row_selectors}.
    Returns `file:symbol`, `file:column` and `file:row` strings for every file in the graph.
    """
    symbols: list[str] = []
    for rel_path, groups in (exports_info.get("exports") or {}).items():
        for kind in ("variables", "functions", "classes"):
            symbols.extend(f"{rel_path}:{name}" for name in groups.get(kind, []))
    columns: list[str] = []
    rows: list[str] = []
    for rel_path, schema in (exports_info.get("csv_schemas") or {}).items():
        columns.extend(f"{rel_path}:{col}" for col in schema.get("columns", []))
        rows.extend(f"{rel_path}:{row}" for row in schema.get("row_selectors", []))
    return {
        "available_ast_symbols": list(dict.fromkeys(symbols)),
        "available_csv_columns": list(dict.fromkeys(columns)),
        "available_csv_rows": list(dict.fromkeys(rows)),
    }
