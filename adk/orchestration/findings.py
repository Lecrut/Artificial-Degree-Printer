"""Findings as the repairing agent needs them (Audit §XI, B0-B2): each one names its file, the symbol and the line
of code it is about, without the noise of the tool that found it, and each one once.

2026-11-18: "config.py:28:32 F821 Undefined name `self`" named no function and showed no code; three repairs of
config.py changed other symbols than the one with the error. Doctest reports were mostly frames of doctest.py.

Only deterministic findings come here (B0): the verification keeps the opinions of model auditors as warnings."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

_RUFF = re.compile(r"^(?P<file>[^\s:][^:\n]*\.py):(?P<line>\d+):(?P<col>\d+): (?P<code>[A-Z]+\d+) (?P<msg>.+)$", re.M)
_PYTEST_SECTION = re.compile(r"\n_{3,} (.+?) _{3,}\n")
_PYTEST_FRAME = re.compile(r"^(?P<file>[^\s:][^:\n]*\.py):(?P<line>\d+): in (?P<func>\S+)$", re.M)
_PYTEST_EXC = re.compile(r"^E\s+(?P<exc>[A-Za-z_][\w.]*(?:Error|Exception|Exit|Interrupt)\b.*)$", re.M)
_RULE = re.compile(r"^(?P<rule>[A-Z][A-Z_]+) \[(?P<file>[^\]]+)\]: (?P<detail>.*)$", re.S)
_SYMBOL_IN_DETAIL = re.compile(r"^- (?P<symbol>[A-Za-z_][\w.]*): ", re.M)


@dataclass(frozen=True)
class Finding:
    source: str  # ruff | pytest | spec | other
    text: str
    file: str = ""
    symbol: str = ""
    line: int = 0
    code: str = ""

    def __str__(self) -> str:
        place = self.file
        if self.symbol:
            place += f" > {self.symbol}"
        if self.line:
            place += f", line {self.line}"
        if self.code:
            place += f": `{self.code}`"
        return f"{place} -- {self.text}" if place else self.text


def locate(workspace: Path, rel: str, line: int) -> tuple[str, str]:
    """(innermost function/class around `line` as `Class.method`, the code on that line) of a workspace file."""
    path = workspace / rel
    if not path.is_file():
        return "", ""
    source = path.read_text(encoding="utf-8", errors="replace")
    lines = source.splitlines()
    code = lines[line - 1].strip() if 0 < line <= len(lines) else ""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "", code

    def _walk(nodes: list[ast.stmt], prefix: str) -> str:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.lineno <= line <= (node.end_lineno or node.lineno):
                name = f"{prefix}{node.name}"
                return _walk(node.body, f"{name}.") or name
        return ""

    return _walk(tree.body, ""), code


def _relative(raw: str, workspace: Path) -> str:
    """Workspace-relative path of a file a tool printed, or "" for a file outside the workspace."""
    text = raw.replace("\\", "/").strip()
    root = workspace.resolve().as_posix()
    if text.startswith(root + "/"):
        return text[len(root) + 1:]
    if "/workspace/" in text:
        text = text.rsplit("/workspace/", 1)[-1]
    if text.startswith("/") or re.match(r"^[A-Za-z]:/", text) or "site-packages" in text:
        return ""
    return text if (workspace / text).is_file() else ""


def _from_ruff(issue: str, workspace: Path) -> list[Finding]:
    found = []
    for m in _RUFF.finditer(issue.removeprefix("Ruff lint failure:").lstrip()):
        rel = _relative(m["file"], workspace) or m["file"]
        symbol, code = locate(workspace, rel, int(m["line"]))
        found.append(Finding("ruff", f"{m['code']} {m['msg'].strip()}", rel, symbol, int(m["line"]), code))
    return found


def _from_pytest(issue: str, workspace: Path) -> list[Finding]:
    """One finding per failed test: the deepest frame in the workspace (the code that raised, else the test) and
    the exception line."""
    parts = _PYTEST_SECTION.split(issue)
    found = []
    for name, body in zip(parts[1::2], parts[2::2]):
        frames = [(f, rel) for f in _PYTEST_FRAME.finditer(body) if (rel := _relative(f["file"], workspace))]
        excs = _PYTEST_EXC.findall(body)
        exc = excs[-1].strip() if excs else "failed"
        if not frames:
            found.append(Finding("pytest", f"{name.strip()}: {exc}"))
            continue
        frame, rel = frames[-1]
        symbol, code = locate(workspace, rel, int(frame["line"]))
        found.append(Finding("pytest", f"{name.strip()}: {exc}", rel, symbol or frame["func"], int(frame["line"]), code))
    return found


def _from_rule(issue: str) -> list[Finding]:
    """`RULE [file]: detail` of the spec gate and the oracles; per-example lines (`- Symbol: ...`) name symbols."""
    m = _RULE.match(issue.strip())
    if m is None:
        return []
    symbols = _SYMBOL_IN_DETAIL.findall(m["detail"])
    detail = m["detail"].strip()
    if len(set(symbols)) == 1:
        return [Finding("spec", f"{m['rule']}: {detail}", m["file"], symbols[0])]
    return [Finding("spec", f"{m['rule']}: {detail}", m["file"])]


def repair_findings(issues: list[object], workspace: Path) -> list[Finding]:
    """The deterministic findings of a verification, located and each once."""
    found: list[Finding] = []
    for raw in issues:
        issue = str(raw)
        if issue.startswith("Ruff lint failure"):
            found += _from_ruff(issue, workspace) or [Finding("ruff", issue[:600])]
        elif issue.startswith("Pytest failure") and "no tests ran" not in issue:
            found += _from_pytest(issue, workspace) or [Finding("pytest", issue[:800])]
        else:
            found += _from_rule(issue) or [Finding("other", issue[:800])]
    unique: dict[tuple[str, str, int, str], Finding] = {}
    for f in found:
        unique.setdefault((f.file, f.symbol, f.line, f.text), f)
    return list(unique.values())


def focus_symbols(findings: list[Finding], target: str) -> list[str]:
    """The symbols of `target` a repair has to change: those the findings name (a method keeps its class prefix)."""
    return sorted({f.symbol for f in findings if f.file == target and f.symbol})


def symbol_sources(workspace: Path, rel: str, symbols: list[str]) -> dict[str, str]:
    """Current source of each symbol (`name` or `Class.method`) of a workspace file."""
    path = workspace / rel
    if not path.is_file() or not symbols:
        return {}
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    out: dict[str, str] = {}

    def _walk(nodes: list[ast.stmt], prefix: str) -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{node.name}"
                if name in symbols:
                    out[name] = ast.get_source_segment(source, node) or ""
                if isinstance(node, ast.ClassDef):
                    _walk(node.body, f"{name}.")

    _walk(tree.body, "")
    return out
