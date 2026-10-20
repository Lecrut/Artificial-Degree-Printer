from __future__ import annotations

import ast
import csv
import re
from pathlib import Path
from typing import Any

from adk.core.models import resolve_adk_path


def _lookup_ast_value(py_file: Path, symbol_name: str) -> tuple[bool, Any]:
    """Extract constant value or function/class signature from a Python file's AST."""
    if not py_file.exists():
        return False, f"File '{py_file.name}' does not exist"
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, f"SyntaxError in '{py_file.name}': {exc}"

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol_name:
                    try:
                        return True, ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        return True, ast.unparse(node.value)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol_name:
            return True, node.name

    return False, f"Symbol '{symbol_name}' not found in '{py_file.name}'"


def _lookup_csv_value(csv_file: Path, column_spec: str) -> tuple[bool, Any]:
    """Extract the latest row value for a given column in a CSV file."""
    if not csv_file.exists():
        return False, f"CSV file '{csv_file.name}' does not exist"

    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
        if not reader:
            return False, f"CSV file '{csv_file.name}' is empty"
        last_row = reader[-1]
        if column_spec not in last_row:
            return False, f"Column '{column_spec}' not found in '{csv_file.name}'"
        return True, last_row[column_spec]


def compile_symbolic_references(
    doc_path: str | Path,
    workspace_dir: str | Path = "workspace",
    write_compiled: bool = True,
) -> dict[str, Any]:
    """Resolve \\ref_ast{file:symbol} and \\ref_csv{file:column} tags and verify CSV vs Python timestamps."""
    w_dir = resolve_adk_path(workspace_dir)
    d_path = Path(doc_path)
    if not d_path.exists():
        d_path = w_dir / doc_path

    if not d_path.exists():
        return {
            "status": "FAIL",
            "errors": [f"Document file not found: {doc_path}"],
            "resolved_references": {},
            "stale_csv_files": [],
            "compiled_text": "",
        }

    text = d_path.read_text(encoding="utf-8")
    errors: list[str] = []
    resolved: dict[str, Any] = {}
    stale_csv_files: list[str] = []

    py_files = [p for p in w_dir.rglob("*.py") if "__pycache__" not in p.parts]
    latest_py_mtime = max((p.stat().st_mtime for p in py_files), default=0.0)

    def _replace_ast(match: re.Match[str]) -> str:
        rel_file = match.group(1).strip()
        sym = match.group(2).strip()
        key = f"\\ref_ast{{{rel_file}:{sym}}}"
        ok, val = _lookup_ast_value(w_dir / rel_file, sym)
        if not ok:
            errors.append(str(val))
            return key
        resolved[key] = val
        return str(val)

    def _replace_csv(match: re.Match[str]) -> str:
        rel_file = match.group(1).strip()
        col = match.group(2).strip()
        key = f"\\ref_csv{{{rel_file}:{col}}}"
        csv_path = w_dir / rel_file
        ok, val = _lookup_csv_value(csv_path, col)
        if not ok:
            errors.append(str(val))
            return key
        if csv_path.exists() and latest_py_mtime > 0 and csv_path.stat().st_mtime + 1e-6 < latest_py_mtime:
            stale_msg = f"CSV file '{rel_file}' is older than Python source code in workspace."
            stale_csv_files.append(rel_file)
            errors.append(stale_msg)
        resolved[key] = val
        return str(val)

    compiled_text = re.sub(r"\\ref_ast\{([^:}]+):([^}]+)\}", _replace_ast, text)
    compiled_text = re.sub(r"\\ref_csv\{([^:}]+):([^}]+)\}", _replace_csv, compiled_text)

    if write_compiled and not errors:
        compiled_out = d_path.with_name(f"{d_path.stem}.compiled{d_path.suffix}")
        compiled_out.write_text(compiled_text, encoding="utf-8")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "resolved_references": resolved,
        "stale_csv_files": stale_csv_files,
        "compiled_text": compiled_text,
    }

