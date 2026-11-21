"""Deterministic oracles Φ that need execution (Audit VI §VII.12.7). The static part of Φ_I is `observe.diff`."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from adk.hypergraph.model import Hypergraph, Violation
from adk.tools.verification.contract_check import stub_source

_ALLOWED_ON_STUBS = ("NotImplementedError",)


_BEHAVIOUR_PROBE = r"""
import ast, doctest, importlib, json, math, os, re, sys, traceback
root, dotted, examples = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
sys.path.insert(0, root)
mod = importlib.import_module(dotted)
_NP = re.compile(r"np\.(?:float|int|uint|bool)\w*\(([^()]*)\)")


def _value(text):
    try:
        return ast.literal_eval(_NP.sub(r"\1", text.strip()).replace("np.True_", "True").replace("np.False_", "False"))
    except Exception:
        return None


def _close(a, b):
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(map(_close, a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-3, abs_tol=1e-6)
    return a == b


class Checker(doctest.OutputChecker):
    # A number is the same number however it is printed: `0` is `0.0`, `5.8284` is `5.828427`, `np.float64(0.5)`
    # is `0.5` (2026-11-21, 03: `expected 0.0, got 0` was charged to the coder as a behaviour mismatch).
    def check_output(self, want, got, optionflags):
        if super().check_output(want, got, optionflags):
            return True
        w, g = _value(want), _value(got)
        return w is not None and g is not None and _close(w, g)


class Runner(doctest.DocTestRunner):
    # One record per failed example, with where it failed: the text report of doctest is mostly its own frames.
    def report_failure(self, out, test, example, got):
        self.fails.append({"example": example.source.strip(), "expected": example.want.strip(), "got": got.strip(),
                           "earlier_failed": bool(self.fails)})

    def report_unexpected_exception(self, out, test, example, exc_info):
        frames = [f for f in traceback.extract_tb(exc_info[2]) if not f.filename.endswith("doctest.py")]
        last = frames[-1] if frames else None
        in_example = last is not None and last.filename.startswith("<doctest")
        where = None
        if last is not None and not in_example:
            try:
                rel = os.path.relpath(last.filename, root).replace(os.sep, "/")
            except ValueError:
                rel = last.filename
            where = {"file": rel, "line": last.lineno, "function": last.name, "code": (last.line or "").strip()}
        self.fails.append({"example": example.source.strip(), "exception": f"{exc_info[0].__name__}: {exc_info[1]}"[:300],
                           "exception_type": exc_info[0].__name__, "in_example": in_example, "where": where,
                           "earlier_failed": bool(self.fails)})


failures = []
parser = doctest.DocTestParser()
for i, text in enumerate(examples):
    runner = Runner(checker=Checker(), optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    runner.fails = []
    runner.run(parser.get_doctest(text, dict(vars(mod)), f"example{i}", None, 0), out=lambda _s: None, clear_globs=True)
    failures += runner.fails
print(json.dumps(failures))
"""


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


def check_behaviour(workspace: str | Path, rel: str, spec: dict, timeout: int = 120) -> list[Violation]:
    """Φ_I.5: the doctest examples of σ — the plan's, not the file's own docstrings — run on the implementation."""
    examples = [e for e in spec.get("behaviour", []) if ">>>" in e]
    path = Path(workspace) / rel
    if not examples or not path.is_file() or is_stub(path.read_text(encoding="utf-8")):
        return []
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _BEHAVIOUR_PROBE, str(Path(workspace).resolve()), spec["import"], json.dumps(examples)],
            capture_output=True, text=True, timeout=timeout, cwd=str(workspace),
        )
        failures = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.stdout.strip() else [proc.stderr[-600:]]
    except subprocess.TimeoutExpired:
        failures = [f"the examples did not finish in {timeout}s"]
    except ValueError:
        failures = [proc.stderr[-600:] or proc.stdout[-600:]]
    if not failures:
        return []
    symbols = list((spec.get("symbols") or {}).keys())
    broken = [f for f in failures if isinstance(f, dict) and _example_is_broken(f, symbols)]
    found: list[Violation] = []
    if broken:
        # The example itself is wrong (a name it never defined): no implementation can satisfy it, so the plan
        # has to change, not the code (2026-11-18: `assert action in valid` in qagent, three coder repairs).
        found.append(Violation(
            "SPEC_EXAMPLE_INVALID",
            "the interface's example cannot pass with any implementation:\n" + "\n".join(_example_text(f, symbols) for f in broken[:3]),
            rel, rel,
        ))
    rest = [f for f in failures if f not in broken]
    if rest:
        found.append(Violation(
            "BEHAVIOUR_MISMATCH",
            "the implementation does not give the results the interface specifies:\n" + "\n".join(_example_text(f, symbols) for f in rest[:4]),
            rel, rel,
        ))
    return found


def _example_is_broken(failure: dict, symbols: list[str]) -> bool:
    """The example's own code raised a NameError or SyntaxError, or called a method the interface does not declare
    (which the write gate refuses to add: 2026-11-21, 03 `algo.neighbors(3, 3)`), and no earlier example of it
    failed (an earlier failure can leave a name undefined)."""
    if not failure.get("in_example") or failure.get("earlier_failed"):
        return False
    missing = re.search(r"has no attribute '(\w+)'", str(failure.get("exception", "")))
    if failure.get("exception_type") == "AttributeError" and missing:
        name = missing.group(1)
        return f".{name}(" in str(failure.get("example", "")) and name not in {s.rsplit(".", 1)[-1] for s in symbols}
    return failure.get("exception_type") in ("NameError", "SyntaxError")


def _example_symbol(example: str, symbols: list[str]) -> str:
    """The planned symbol an example exercises: the last one whose name it calls."""
    called = [m for m in symbols if f"{m.rpartition('.')[2]}(" in example]
    return called[-1] if called else ""


def _example_text(failure: dict | str, symbols: list[str]) -> str:
    """One failed example as the agent needs it: the symbol, the example, and expected/got or the exception with
    the line of the implementation where it was raised. No frames of doctest itself."""
    if not isinstance(failure, dict):
        return str(failure)[-600:]
    example = failure.get("example", "")
    symbol = _example_symbol(example, symbols)
    head = f"- {symbol + ': ' if symbol else ''}example `{example[:200]}`"
    if "exception" not in failure:
        return f"{head} expected `{failure.get('expected', '')[:200]}`, got `{failure.get('got', '')[:200]}`"
    where = failure.get("where") or {}
    place = (
        f" in {where.get('file')} > {where.get('function')}, line {where.get('line')}: `{where.get('code', '')[:160]}`"
        if where else " in the example's own code"
    )
    note = " (after an earlier example of the same docstring failed)" if failure.get("earlier_failed") else ""
    return f"{head} raised {failure['exception']}{place}{note}"


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
