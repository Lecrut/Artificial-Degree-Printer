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
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == symbol_name:
            if node.value is not None:
                try:
                    return True, ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    return True, ast.unparse(node.value)
            return True, symbol_name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol_name:
            return True, node.name

    return False, f"Symbol '{symbol_name}' not found in '{py_file.name}'"


def _lookup_csv_value(csv_file: Path, column_spec: str) -> tuple[bool, Any]:
    """Extract a CSV value by 'column' (latest row) or 'row_selector:column' (specific method/metric row or index)."""
    if not csv_file.exists():
        return False, f"CSV file '{csv_file.name}' does not exist"

    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
        if not reader:
            return False, f"CSV file '{csv_file.name}' is empty"

        if ":" in column_spec:
            row_selector, col_name = [part.strip() for part in column_spec.split(":", 1)]
            target_row: dict[str, Any] | None = None
            try:
                row_idx = int(row_selector)
                if -len(reader) <= row_idx < len(reader):
                    target_row = reader[row_idx]
            except ValueError:
                pass

            if target_row is None:
                for row in reader:
                    if any(str(v).strip() == row_selector for v in row.values() if v is not None):
                        target_row = row
                        break
            if target_row is None:
                for row in reader:
                    if any(str(v).strip().lower() == row_selector.lower() for v in row.values() if v is not None):
                        target_row = row
                        break

            if target_row is None:
                return False, f"Row selector '{row_selector}' not found in '{csv_file.name}'"
            if col_name not in target_row:
                match_col = next((k for k in target_row if k.strip().lower() == col_name.strip().lower()), None)
                if match_col is not None:
                    col_name = match_col
                else:
                    return False, f"Column '{col_name}' not found in '{csv_file.name}'"
            return True, target_row[col_name]

        last_row = reader[-1]
        if column_spec not in last_row:
            match_col = next((k for k in last_row if k.strip().lower() == column_spec.strip().lower()), None)
            if match_col is not None:
                column_spec = match_col
            else:
                return False, f"Column '{column_spec}' not found in '{csv_file.name}'"
        return True, last_row[column_spec]


FIGURE_EXTENSIONS: tuple[str, ...] = (".pdf", ".png", ".svg", ".tex", ".eps", ".jpg", ".jpeg", ".py")


def _lookup_fig_value(w_dir: Path, doc_text: str, target_spec: str) -> tuple[bool, str]:
    """Verify that a figure/plot file or TikZ diagram referenced by \\ref_fig{target} exists."""
    clean_target = target_spec.strip()
    if not clean_target:
        return False, "Empty \\ref_fig{} target."

    direct_path = w_dir / clean_target
    if direct_path.exists() and direct_path.is_file():
        return True, f"[Ryc. {clean_target}]"

    target_stem = Path(clean_target).stem
    for ext in FIGURE_EXTENSIONS:
        candidate = w_dir / f"{target_stem}{ext}"
        if candidate.exists() and candidate.is_file():
            return True, f"[Ryc. {clean_target}]"

    if "\\begin{tikzpicture}" in doc_text:
        if (
            f"\\label{{{clean_target}}}" in doc_text
            or "tikz" in clean_target.lower()
            or clean_target in doc_text.split("\\begin{tikzpicture}", 1)[1]
        ):
            return True, f"[Ryc. {clean_target}]"

    return False, f"Figure reference '{clean_target}' not found in workspace."



AI_FLUFF_BLACKLIST: tuple[str, ...] = (
    "przełomowe podejście",
    "rewolucyjny algorytm",
    "jak powszechnie wiadomo",
    "wybitne rezultaty",
    "niezwykle fascynujący",
    "bez wątpienia najlepszy",
    "groundbreaking",
    "revolutionary approach",
    "as is well known",
    "delve into",
    "testament to",
)


def compile_symbolic_references(
    doc_path: str | Path,
    workspace_dir: str | Path = "workspace",
    write_compiled: bool = True,
) -> dict[str, Any]:
    """Resolve \\ref_ast{file:symbol} and \\ref_csv{file:[row:]column} tags, verify timestamps, diagrams, citations, and AI fluff."""
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
            "fluff_detected": [],
            "compiled_text": "",
        }

    text = d_path.read_text(encoding="utf-8")
    errors: list[str] = []
    resolved: dict[str, Any] = {}
    stale_csv_files: list[str] = []

    py_files = [
        p
        for p in w_dir.rglob("*.py")
        if "__pycache__" not in p.parts and "benchmarks" not in p.parts
    ]
    latest_py_mtime = max((p.stat().st_mtime for p in py_files), default=0.0)

    def _replace_ast(match: re.Match[str]) -> str:
        rel_file = match.group(1).strip()
        sym = match.group(2).strip()
        key = f"\\ref_ast{{{rel_file}:{sym}}}"
        target_py = w_dir / rel_file
        if not target_py.exists() and (w_dir / "code" / rel_file).exists():
            target_py = w_dir / "code" / rel_file
        ok, val = _lookup_ast_value(target_py, sym)
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
        if not csv_path.exists() and (w_dir / "results" / rel_file).exists():
            csv_path = w_dir / "results" / rel_file
        ok, val = _lookup_csv_value(csv_path, col)
        if not ok:
            errors.append(str(val))
            return key
        if csv_path.exists() and latest_py_mtime > 0 and csv_path.stat().st_mtime + 1e-6 < latest_py_mtime:
            stale_msg = f"CSV file '{rel_file}' is older than Python source code in workspace."
            if rel_file not in stale_csv_files:
                stale_csv_files.append(rel_file)
            errors.append(stale_msg)
        resolved[key] = val
        return str(val)

    def _replace_fig(match: re.Match[str]) -> str:
        fig_target = match.group(1).strip()
        key = f"\\ref_fig{{{fig_target}}}"
        ok, val = _lookup_fig_value(w_dir, text, fig_target)
        if not ok:
            errors.append(str(val))
            return key
        resolved[key] = val
        if d_path.suffix == ".tex":
            stem = Path(fig_target).stem
            if stem in ("comparison_chart", "figure", "arch_tikz"):
                return f"\\ref{{fig:{stem}}}"
            return str(val).replace("_", "\\_")
        return str(val)

    compiled_text = re.sub(r"\\ref_ast\{([^:}]+):([^}]+)\}", _replace_ast, text)
    compiled_text = re.sub(r"\\ref_csv\{([^:}]+):([^}]+)\}", _replace_csv, compiled_text)
    compiled_text = re.sub(r"\\ref_fig\{([^}]+)\}", _replace_fig, compiled_text)


    # Check for malformed \ref_ast{...} or \ref_csv{...} missing a ':' separator
    for bad_tag in re.findall(r"\\ref_(?:ast|csv)\{[^:}]+\}", text):
        errors.append(f"Malformed symbolic tag missing ':' separator: {bad_tag}")

    # Check balanced TikZ environments if present
    tikz_begins = len(re.findall(r"\\begin\{tikzpicture\}", compiled_text))
    tikz_ends = len(re.findall(r"\\end\{tikzpicture\}", compiled_text))
    if tikz_begins != tikz_ends:
        errors.append(f"Unbalanced TikZ environment: {tikz_begins} \\begin vs {tikz_ends} \\end.")

    # Check \cite{...} keys against .bib files if any .bib file exists in workspace
    bib_files = (list(w_dir.glob("*.bib")) + list((w_dir / "thesis").glob("*.bib"))) if w_dir.exists() else []
    if bib_files:
        defined_bib_keys: set[str] = set()
        for bf in bib_files:
            bib_text = bf.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"@\w+\{\s*([^,\s]+)\s*,", bib_text):
                defined_bib_keys.add(m.group(1).strip())
        for cite_match in re.finditer(r"\\cite\{([^}]+)\}", compiled_text):
            for raw_key in cite_match.group(1).split(","):
                ckey = raw_key.strip()
                if ckey and ckey not in defined_bib_keys:
                    errors.append(f"Citation key '{ckey}' not found in workspace .bib files.")

    # Scan for blacklisted AI fluff phrases
    lower_compiled = compiled_text.lower()
    fluff_detected = [phrase for phrase in AI_FLUFF_BLACKLIST if phrase in lower_compiled]

    if write_compiled and not errors:
        compiled_out = d_path.with_name(f"{d_path.stem}.compiled{d_path.suffix}")
        compiled_out.write_text(compiled_text, encoding="utf-8")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "resolved_references": resolved,
        "stale_csv_files": stale_csv_files,
        "fluff_detected": fluff_detected,
        "compiled_text": compiled_text,
    }

