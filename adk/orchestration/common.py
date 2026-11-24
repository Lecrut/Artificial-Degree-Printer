"""Module-level helpers and constants shared by the orchestrator and its mixins."""

from __future__ import annotations


import csv
import re
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


# Repairs sent straight back to the failed file's author with the verification findings, before the one
# planner-and-evolution cycle a task gets (Audit IV §IV.7 pkt 6).
FAST_REPAIR_ATTEMPTS = 2


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
    ("torch", "torch", "import torch"),
    ("gym", "gymnasium", "import gymnasium as gym"),
    ("sm", "statsmodels", "import statsmodels.api as sm"),
    ("sympy", "sympy", "import sympy"),
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

# Budgets for findings placed in a prompt, in characters (~4 characters per token). Models have 128k context,
# so keep generous caps that preserve full tracebacks and logs while still bounding runaway outputs.
FINDINGS_BUDGET_CHARS = 60000
LOG_BUDGET_CHARS = 60000


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


def _result_rows(workspace_dir: Path) -> list[dict[str, str]]:
    """Rows with a `metric` of every tidy results file of the workspace (logs and benchmark copies excluded)."""
    rows: list[dict[str, str]] = []
    for csv_path in workspace_dir.rglob("*.csv"):
        rel = csv_path.relative_to(workspace_dir).parts
        if "logs" in rel or "benchmarks" in rel:
            continue
        try:
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows += [row for row in csv.DictReader(handle) if row.get("metric")]
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    return rows


def _degenerate_metrics(workspace_dir: Path) -> list[str]:
    """Metrics that are exactly 0 with no spread over several runs: the pipeline measures nothing (2026-11-23, 01: a
    game environment that never ended the game gave `win_rate` 0.0 in 3 of 3 runs and every gate passed)."""
    found: list[str] = []
    for row in _result_rows(workspace_dir) if workspace_dir.exists() else []:
        try:
            value, spread, runs = float(row["value"]), float(row.get("std_dev") or 0), float(row.get("n_runs") or 0)
        except (KeyError, TypeError, ValueError):
            continue
        if value == 0.0 and spread == 0.0 and runs >= 2:
            found.append(texts.metric_degenerate(str(row["metric"]).strip()))
    return list(dict.fromkeys(found))


def _declared_vs_measured_metrics(declared: list[str], workspace_dir: Path) -> list[str]:
    """Compare the metrics the plan pre-registered with the `metric` column of the tidy results files.

    Deviations are allowed but must be visible: a declared metric that was never measured, or a measured one that
    was never declared, is reported (non-blocking) so the thesis has to explain it.
    """
    if not declared or not workspace_dir.exists():
        return []
    measured = {str(row["metric"]).strip() for row in _result_rows(workspace_dir)}
    if not measured:
        return []  # nothing measured yet: the experiment has not run
    measured_l, declared_l = {m.lower() for m in measured}, {m.strip().lower() for m in declared}
    findings = [texts.metric_not_measured(m) for m in declared if m.strip().lower() not in measured_l]
    findings += [texts.metric_not_declared(m) for m in sorted(measured) if m.lower() not in declared_l]
    return findings


def _normalized_files(llm_output: dict[str, Any]) -> dict[str, Any]:
    """Unambiguous variants of the `files` shape as a list of `{filename, content}` (§XII R3: they were rejected and
    cost a repair attempt): one file answered flat, `files` as `{path: content}`, `files` as one `{filename, content}`."""
    files = llm_output.get("files")
    flat_name = llm_output.get("filename") or llm_output.get("path")
    if not files and flat_name and isinstance(llm_output.get("content"), str):
        files = [{"filename": flat_name, "content": llm_output["content"]}]
    elif isinstance(files, dict):
        files = [files] if ("filename" in files or "path" in files) else [
            {"filename": k, "content": v} for k, v in files.items() if isinstance(v, str)
        ]
    return {**llm_output, "files": files} if files is not llm_output.get("files") else llm_output


def _missing_chapter_tasks(issues_text: str, chapter_titles: dict[int, str]) -> list[dict[str, Any]]:
    """Writer tasks for planned chapters (number -> title from the plan) the defense audit reported as missing."""
    match = texts.MISSING_CHAPTERS_PATTERN.search(issues_text)
    if not match:
        return []
    listed = match.group(1).lower()
    return [
        {
            "task_id": f"GATE_3_CH{number}_FIX",
            "target_node": THESIS_FILE,
            "assigned_agent": "seed_writer",
            "description": templates.titled_chapter_task(number, title),
            "status": "TODO",
            "covers": texts.chapter_covers(number),
        }
        for number, title in sorted(chapter_titles.items())
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
