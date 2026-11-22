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


def stub_functions(source: str) -> list[str]:
    """Functions and methods (`Class.method`) without an implementation: their body (besides the docstring) is
    empty, `...`, `pass` or only `raise NotImplementedError` (the e2e run: a body of `...` passed as implemented)."""
    tree = ast.parse(source)
    owner = {id(item): f"{node.name}." for node in ast.walk(tree) if isinstance(node, ast.ClassDef) for item in node.body}
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = [
                s for s in node.body
                if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) and not isinstance(s, ast.Pass)
            ]
            if not body or (len(body) == 1 and isinstance(body[0], ast.Raise) and "NotImplementedError" in ast.unparse(body[0])):
                found.append(owner.get(id(node), "") + node.name)
    return found


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
