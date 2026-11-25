"""A workspace with results and a report, as a test of pointers to results needs it."""

from __future__ import annotations

from pathlib import Path

_CSV = "method,metric,value\nq_learning,win_rate,0.9\nbaseline,win_rate,0.4\n"


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "results.csv").write_text(_CSV, encoding="utf-8")
    return tmp_path


def _report(issues: list[str]) -> dict:
    return {"failed_file": "thesis.md", "issues": issues}
