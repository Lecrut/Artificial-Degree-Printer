"""The sketch of a module (stage 2 of planning, §XXIX D5): the module author declares names, signatures and docstrings
in a JSON object that has no field for a body, and the harness builds the interface source from it. Until 2026-11-25
the author returned a Python file, finished functions with full bodies (57-124 lines per module in 02 and 03), and
the harness threw them away at the stub: the coder wrote the same function again, the tester read the discarded
body in σ. A body has no way into a sketch, so there is nothing to cut afterwards.

Sketch: {"docstring", "imports": [str], "constants": [{"name","type","value"} | str],
"functions": [{"signature","docstring","decorators"}], "classes": [{"name","bases","docstring","decorators",
"attributes": [str | {"name","type","value"}], "methods": [function]}]}. `needs` is not part of it (the caller reads it)."""

from __future__ import annotations

import ast
from textwrap import indent
from typing import Any

_PAIRS = {"(": ")", "[": "]", "{": "}"}


def _header(signature: str) -> tuple[bool, str]:
    """(async, `name(params) -> return`) of a signature a model wrote: a leading `def`/`async def` and the colon that
    ends the header are taken off, and so is every line of a body written after it."""
    text = signature.strip()
    is_async = text.startswith("async ")
    text = text.removeprefix("async ").strip().removeprefix("def ").strip()
    depth, closed = 0, False
    for i, char in enumerate(text):
        depth += (char in _PAIRS) - (char in _PAIRS.values())
        closed = closed or (char == ")" and depth == 0)
        if char == ":" and depth == 0 and closed:
            return is_async, text[:i].strip()
    return is_async, text


def _doc(text: Any, pad: str) -> list[str]:
    """The docstring as a triple-quoted line block; backslashes and quotes inside it cannot end it early."""
    body = str(text or "").strip().replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    if body.endswith('"'):
        body = body[:-1] + '\\"'
    return [indent(f'"""{body}"""', pad)] if body else []


def _decorators(item: dict[str, Any], pad: str) -> list[str]:
    raw = item.get("decorators")
    return [pad + "@" + str(d).strip().removeprefix("@") for d in (raw if isinstance(raw, list) else []) if str(d).strip()]


def _function(item: dict[str, Any], pad: str) -> list[str]:
    is_async, header = _header(str(item.get("signature") or ""))
    if not header:
        return []
    keyword = "async def" if is_async else "def"
    return [*_decorators(item, pad), f"{pad}{keyword} {header}:", *_doc(item.get("docstring"), pad + "    "), f"{pad}    ..."]


def _assignment(item: Any) -> str:
    """`NAME: type = value` from a dict (or the text a model wrote instead)."""
    if not isinstance(item, dict):
        return str(item).strip()
    name, kind, value = (str(item.get(k) or "").strip() for k in ("name", "type", "value"))
    try:
        ast.parse(value, mode="eval") if value else None
    except SyntaxError:
        value = repr(value)  # a small model writes a path or a word without quotes: it means a string
    return "".join([name, f": {kind}" if kind else "", f" = {value}" if value else ""])


def _class(item: dict[str, Any]) -> list[str]:
    bases = item.get("bases")
    header = f"class {str(item.get('name') or '').strip()}" + (f"({', '.join(map(str, bases))})" if isinstance(bases, list) and bases else "")
    attributes = [a for a in map(_assignment, item.get("attributes") or []) if a]
    methods = [line for m in item.get("methods") or [] if isinstance(m, dict) for line in (_function(m, "    ") + [""])]
    body = [*_doc(item.get("docstring"), "    "), *[f"    {a}" for a in attributes], *([""] if attributes and methods else []), *methods]
    return [*_decorators(item, ""), header + ":", *(body or ["    ..."])]


def sketch_to_source(raw: Any) -> str:
    """The interface source of a sketch, every body `...`; empty when the sketch declares nothing."""
    if not isinstance(raw, dict):
        return ""
    constants = [a for a in map(_assignment, raw.get("constants") or []) if a]
    classes = [c for c in raw.get("classes") or [] if isinstance(c, dict) and str(c.get("name") or "").strip()]
    functions = [f for f in raw.get("functions") or [] if isinstance(f, dict)]
    if not (constants or classes or functions):
        return ""
    blocks = ["\n".join(_doc(raw.get("docstring"), ""))]
    blocks.append("\n".join(str(i).strip() for i in raw.get("imports") or [] if str(i).strip()))
    blocks.append("\n".join(constants))
    blocks += ["\n".join(_class(c)).rstrip() for c in classes]
    blocks += ["\n".join(_function(f, "")) for f in functions]
    return "\n\n\n".join(b for b in blocks if b.strip()) + "\n"


def _function_sketch(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    item: dict[str, Any] = {
        "signature": f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}{node.name}({ast.unparse(node.args)}){returns}",
        "docstring": ast.get_docstring(node) or "",
    }
    if node.decorator_list:
        item["decorators"] = [ast.unparse(d) for d in node.decorator_list]
    return item


def _class_sketch(node: ast.ClassDef) -> dict[str, Any]:
    item: dict[str, Any] = {
        "name": node.name,
        "bases": [ast.unparse(b) for b in node.bases] + [ast.unparse(k) for k in node.keywords],
        "docstring": ast.get_docstring(node) or "",
        "attributes": [ast.unparse(s) for s in node.body if isinstance(s, (ast.AnnAssign, ast.Assign))],
        "methods": [_function_sketch(s) for s in node.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))],
    }
    if node.decorator_list:
        item["decorators"] = [ast.unparse(d) for d in node.decorator_list]
    return item


def source_to_sketch(source: str) -> dict[str, Any]:
    """The sketch of existing source (an accepted interface, or a module of the project): its declarations, none of
    its bodies, nothing that is not a declaration. `{}` when the source does not parse."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    return {
        "docstring": ast.get_docstring(tree) or "",
        "imports": [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))],
        "constants": [ast.unparse(n) for n in tree.body if isinstance(n, (ast.AnnAssign, ast.Assign))],
        "functions": [_function_sketch(n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
        "classes": [_class_sketch(n) for n in tree.body if isinstance(n, ast.ClassDef)],
    }
