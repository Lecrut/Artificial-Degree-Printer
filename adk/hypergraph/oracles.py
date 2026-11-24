"""Deterministic oracles Φ that need execution (Audit VI §VII.12.7). The static part of Φ_I is `observe.diff`."""

from __future__ import annotations

import ast
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from adk.hypergraph.model import Hypergraph, Violation
from adk.tools.verification.contract_check import stub_source

_ALLOWED_ON_STUBS = ("NotImplementedError",)


def _empty_body(node: ast.AST) -> bool:
    """A body of nothing but a docstring, `...`, `pass` or one `raise NotImplementedError`."""
    body = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) and not isinstance(s, ast.Pass)]
    return not body or (len(body) == 1 and isinstance(body[0], ast.Raise) and "NotImplementedError" in ast.unparse(body[0]))


def stub_functions(source: str) -> list[str]:
    """Functions and methods (`Class.method`) without an implementation: their body (besides the docstring) is
    empty, `...`, `pass` or only `raise NotImplementedError` (the e2e run: a body of `...` passed as implemented).

    Two designs are not stubs (2026-11-24, 01: `agents.py` was refused nine times for them): an abstract method of a
    base class (an ABC/Protocol, an `@abstractmethod`, or a class another class of the file inherits from), and a
    `pass` body of a method annotated `-> None` in a class that implements another method (a no-op such as
    `RandomAgent.update`). A class of stubs only, and `...`, stay stubs."""
    tree = ast.parse(source)
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    owner = {id(item): cls for cls in classes for item in cls.body}
    inherited = {ast.unparse(b) for cls in classes for b in cls.bases}

    def is_design(node: ast.AST, cls: ast.ClassDef | None) -> bool:
        if cls is None:
            return False
        bases = {ast.unparse(b).rpartition(".")[2] for b in cls.bases}
        if cls.name in inherited or bases & {"ABC", "Protocol"} or any("abstractmethod" in ast.unparse(d) for d in node.decorator_list):
            return True
        no_op = ast.unparse(node.returns) == "None" if node.returns is not None else False
        only_pass = any(isinstance(s, ast.Pass) for s in node.body) and not any(isinstance(s, ast.Raise) for s in node.body)
        siblings = [m for m in cls.body if m is not node and isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        return no_op and only_pass and any(not _empty_body(m) for m in siblings)

    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _empty_body(node):
            cls = owner.get(id(node))
            if not is_design(node, cls):
                found.append((f"{cls.name}." if cls else "") + node.name)
    return found


def _own_nodes(func: ast.AST) -> list[ast.AST]:
    """Nodes of a function's own body, without nested functions, lambdas and classes (their `return` is theirs)."""
    found: list[ast.AST] = []
    todo = list(getattr(func, "body", []))
    while todo:
        node = todo.pop()
        found.append(node)
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            todo.extend(ast.iter_child_nodes(node))
    return found


def _asserts(nodes: list[ast.AST], helpers: set[str]) -> bool:
    for node in nodes:
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            owner = ast.unparse(node.func.value) if isinstance(node.func, ast.Attribute) else ""
            if name.startswith("assert") or name in helpers or (owner == "pytest" and name in ("raises", "warns", "approx", "fail")):
                return True
    return False


def assertionless_tests(source: str) -> list[str]:
    """Test functions (`test_*`, also in `Test*` classes) that check nothing: no `assert`, `pytest.raises/warns/approx/fail`,
    `assert_*` / `self.assert*` call and no call of a function of the same file that asserts. Pytest passes such a test
    (2026-11-22, 02: a test of comments only made `data_generation.py` with no `return` pass as verified)."""
    tree = ast.parse(source)
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    helpers = {f.name for f in funcs if not f.name.startswith("test_") and any(isinstance(n, ast.Assert) for n in _own_nodes(f))}
    return [f.name for f in funcs if f.name.startswith("test_") and not _asserts(_own_nodes(f), helpers)]


def functions_without_return(source: str) -> list[str]:
    """Functions and methods whose annotation promises a value (not `None`, `NoReturn`, a generator, an abstract or
    overloaded one, a stub) but whose body has no `return <value>` and does not end with `raise`: they always return
    `None` (2026-11-22, 02: `generate_dataset -> Tuple[...]` ended after a loop; the experiment kept being rewritten)."""
    tree = ast.parse(source)
    owner = {id(item): f"{node.name}." for node in ast.walk(tree) if isinstance(node, ast.ClassDef) for item in node.body}
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.returns is None:
            continue
        name = owner.get(id(node), "") + node.name
        annotation = ast.unparse(node.returns)
        decorators = " ".join(ast.unparse(d) for d in node.decorator_list)
        if _empty_body(node) or annotation in ("None", "NoReturn", "Never") or "abstractmethod" in decorators or "overload" in decorators:
            continue
        own = _own_nodes(node)
        if any(isinstance(n, (ast.Yield, ast.YieldFrom)) or (isinstance(n, ast.Return) and n.value is not None) for n in own):
            continue
        if node.body and isinstance(node.body[-1], ast.Raise):
            continue
        found.append(name)
    return found


def static_defects(workspace: str | Path, rel: str, h: Hypergraph) -> list[Violation]:
    """Φ_I.5: a test without a single check, a function that promises a value and never returns one. Both pass
    pytest, so only the write gate can stop them from becoming `verified`."""
    vertex = h.vertices.get(rel)
    path = Path(workspace) / rel
    if vertex is None or not path.is_file():
        return []
    try:
        source = path.read_text(encoding="utf-8")
        if vertex.kind == "test":
            names = assertionless_tests(source)
            rule, detail = "TEST_NO_ASSERTIONS", "these tests check nothing (no `assert`, `pytest.raises`, `pytest.approx`): "
        elif vertex.kind in ("code", "entry"):
            names = functions_without_return(source)
            rule, detail = "FUNCTION_NEVER_RETURNS", "the annotation promises a value, the body has no `return <value>` (is the answer cut off?): "
        else:
            return []
    except SyntaxError:
        return []  # syntax is judged by ruff and pytest, with better messages
    return [Violation(rule, detail + ", ".join(names), rel, rel)] if names else []


def is_stub(source: str) -> bool:
    """True while some function or method has no implementation (see `stub_functions`)."""
    return bool(stub_functions(source))


def validate_test_on_stubs(workspace: str | Path, test_rel: str, h: Hypergraph, timeout: int = 120) -> list[Violation]:
    """Φ_I.4: run a test file against the stubs of every planned module. Each test must fail only with
    `NotImplementedError` (or pass, e.g. on a declared constant). Anything else — a collection error, an
    ImportError, a NameError, a TypeError from a wrong call — is a defect of the test itself, found before any
    implementation exists (02, 2026-11-16: `np` without import, a wrong module path; the repairs went to the coder)."""
    root = Path(workspace)
    with tempfile.TemporaryDirectory(prefix="adk_test_on_stubs_") as tmp:
        sandbox = Path(tmp)
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(root).as_posix()
            target = sandbox / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            vertex = h.vertices.get(rel)
            source = path.read_text(encoding="utf-8")
            if vertex is not None and vertex.kind in ("code", "entry"):
                source = stub_source(source) or source
            target.write_text(source, encoding="utf-8")
        for extra in ("conftest.py", "pytest.ini", "pyproject.toml"):
            if (root / extra).is_file() and not (sandbox / extra).exists():
                shutil.copy2(root / extra, sandbox / extra)
        report = sandbox / "_junit.xml"
        env = {**os.environ, "PYTHONPATH": str(sandbox)}
        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", test_rel, "-q", "-p", "no:cacheprovider", "--import-mode=importlib",
                 f"--junitxml={report}", "--tb=line"],
                cwd=str(sandbox), env=env, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return [Violation("TEST_HANGS_ON_STUBS", f"did not finish in {timeout}s against the stubs", test_rel, test_rel)]
        if not report.exists():
            return [Violation("TEST_INVALID_ON_STUBS", "pytest produced no report (the file does not even collect)", test_rel, test_rel)]
        problems: list[str] = []
        for case in ET.parse(report).getroot().iter("testcase"):
            for outcome in [*case.findall("failure"), *case.findall("error")]:
                message = (outcome.get("message") or outcome.text or "").strip().splitlines()
                first = message[0] if message else "unknown failure"
                if not any(first.startswith(ok) or f"E   {ok}" in (outcome.text or "") for ok in _ALLOWED_ON_STUBS):
                    problems.append(f"{case.get('name') or 'collection'}: {first[:200]}")
    if not problems:
        return []
    return [Violation(
        "TEST_INVALID_ON_STUBS",
        "against the stubs a test may fail only with NotImplementedError; these fail for a reason of their own: "
        + "; ".join(problems[:6]),
        test_rel, test_rel,
    )]


def run_fingerprint(workspace: str | Path, h: Hypergraph) -> str | None:
    """sha256 of the code the experiment runs: every code member of R with its helper files (Φ_R freshness; the
    original E2 contract: the data come from the current version of the code)."""
    if "R:run" not in h.edges:
        return None
    modules = sorted({
        rel
        for member, role in h.edges["R:run"].members.items()
        if role in ("P", "C") and h.vertices.get(member) is not None and h.vertices[member].kind in ("code", "entry")
        for rel in h.files_of(member)
    })
    digest = hashlib.sha256()
    for rel in modules:
        path = Path(workspace) / rel
        digest.update(rel.encode("utf-8") + b"\0" + (path.read_bytes() if path.is_file() else b"<missing>") + b"\0")
    return digest.hexdigest()
