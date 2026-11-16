"""The plan's interfaces: the contract every later task builds on, and the check that task descriptions use it."""

from __future__ import annotations


import ast
import builtins
import keyword
import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.tools.verification.contract_check import is_contract_module, public_api, stub_source


# A name used as code in a task description: `name(` (optionally dotted) or `name` in backticks.
_CODE_NAME = re.compile(r"\b((?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)\(|`((?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)(?:\(\))?`")


_KNOWN_NAMES = set(dir(builtins)) | set(keyword.kwlist) | {"self", "cls", "pytest", "main"}


_FILE_SUFFIXES = {"py", "csv", "md", "json", "txt", "pdf", "png", "svg", "bib", "tex"}


def _plan_interfaces(plan_out: dict[str, Any]) -> dict[str, str]:
    """`interfaces` of a plan: workspace path of a code module -> its interface as Python source (signatures,
    docstrings, constants). Accepts the field at the top level or in `academic_blueprint`, as a mapping or as a
    list of `{file, source}`; entries that are not code modules or do not parse are dropped."""
    blueprint = plan_out.get("academic_blueprint") if isinstance(plan_out.get("academic_blueprint"), dict) else {}
    raw = plan_out.get("interfaces") or blueprint.get("interfaces") or {}
    if isinstance(raw, list):
        raw = {
            item.get("file") or item.get("path") or item.get("filename"): item.get("source") or item.get("code") or item.get("content")
            for item in raw
            if isinstance(item, dict)
        }
    found: dict[str, str] = {}
    for path, source in (raw.items() if isinstance(raw, dict) else []):
        rel = str(path or "").replace("\\", "/").strip()
        while rel.startswith(("./", "workspace/")):
            rel = rel.removeprefix("./").removeprefix("workspace/")
        if is_contract_module(rel) and isinstance(source, str) and stub_source(source) is not None:
            found[rel] = source
    return found


def _interface_gaps(tasks: list[Any], interfaces: dict[str, str]) -> list[str]:
    """What the plan's tasks need from `interfaces` and it lacks: a code module a task targets by path with no
    interface, or a name a task description uses as code that no interface defines (U1, 2026-11-15: tasks named
    `TicTacToeEnv.get_state_hash`, the contract had `GameEnvironment` without it)."""
    gaps: list[str] = []
    descriptions = [str(t.get("description", "")) for t in tasks if isinstance(t, dict)]
    targets = [str(t.get("target_node", "")).replace("\\", "/") for t in tasks if isinstance(t, dict)]
    missing = sorted({rel for rel in targets if is_contract_module(rel)} - set(interfaces))
    if missing:
        gaps.append(texts.modules_without_interface(missing))
    if not interfaces:
        return gaps
    modules = {Path(rel).stem for rel in interfaces}
    defined: set[str] = set()
    for source in interfaces.values():
        defined.update(part for key in (public_api(source) or {}) for part in key.split("."))
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                defined.add(node.attr)
    unknown: set[str] = set()
    for desc in descriptions:
        for match in _CODE_NAME.finditer(desc):
            parts = (match.group(1) or match.group(2)).split(".")
            if len(parts) > 1 and (parts[0] not in defined | modules or parts[-1] in _FILE_SUFFIXES):
                continue  # `np.mean(`, `config.py`: a package or a file name, not the plan's API
            name = parts[-1]
            if name not in defined | modules and name not in _KNOWN_NAMES and not name.startswith("test_"):
                unknown.add(name)
    if unknown:
        gaps.append(texts.names_outside_interfaces(sorted(unknown)))
    return gaps
