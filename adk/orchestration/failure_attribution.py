"""Who failed: the workspace file and author a pytest failure points to, from its traceback."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_TB_FRAME = re.compile(r"^(\S+?\.py):\d+: in ", re.MULTILINE)
_HANG_FRAME = re.compile(r'^File "([^"]+?\.py)", line (?:\d+|\?+) in ', re.MULTILINE)
_TB_EXC = re.compile(r"^E\s+([A-Za-z_][\w.]*)", re.MULTILINE)
# Errors raised at the test's own call site: the test uses the API wrongly (wrong arguments, a name the module
# does not have). Anything else that surfaces only in the test frame (a failed assertion) is a wrong result
# of the code under test.
_TEST_MISUSE = {"TypeError", "AttributeError", "NameError", "ImportError", "ModuleNotFoundError", "SyntaxError"}


def _is_test(rel: str) -> bool:
    name = Path(rel).name
    return rel.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def _pytest_culprits(issue: str) -> list[tuple[str, bool]]:
    """Per failed test in a `--tb=short` pytest report: (deepest workspace frame, whether that is the code under
    test). A frame below the test means the code raised; only the test frame means either the test misuses the
    API (`_TEST_MISUSE`, culprit = test) or the code returned a wrong value (assertion, culprit = code; the
    caller resolves which module from the hypergraph).

    2026-11-14: the first file named in the findings was taken as the culprit, pytest always names the test file
    first, and 77 repairs of failed assertions went to the tester while the bug sat in the module."""
    if "a test hung and was stopped" in issue:
        # faulthandler's dump, newest frame first, has no pytest sections: the file of the newest frame is the
        # culprit (2026-11-23, 01: a test whose own mock recursed was charged to `experiment.py`).
        frames = [f.replace("\\", "/") for f in _HANG_FRAME.findall(issue)]
        return [(frames[0], False)] if frames else []
    found: list[tuple[str, bool]] = []
    for section in re.split(r"\n_{3,} .+? _{3,}\n", issue)[1:]:
        frames = [f.replace("\\", "/") for f in _TB_FRAME.findall(section)]
        if not frames:
            continue
        code_frames = [f for f in frames if not _is_test(f)]
        if code_frames:
            found.append((code_frames[-1], True))
            continue
        exc = (_TB_EXC.findall(section) or [""])[-1].split(".")[-1].rstrip(":")
        found.append((frames[0], exc not in _TEST_MISUSE))
    return found


_PY_FRAME = re.compile(r'File "([^"]+?\.py)", line \d+')


def _traceback_culprit(text: str, workspace: Path) -> str | None:
    """The deepest workspace file in a Python traceback (a run of the experiment or of the plots function).
    2026-11-20: `plots.py` raised, the error was charged to the entrypoint and three repairs rewrote a correct file."""
    root = workspace.resolve()
    for raw in reversed(_PY_FRAME.findall(text)):
        try:
            return Path(raw).resolve().relative_to(root).as_posix()
        except (ValueError, OSError):
            continue
    return None


def _suspect_test(h: Any, module: str, test_file: str) -> bool:
    """A failed assertion seen only in the test frame blames the unverified one of the pair (§XIV Q2): the module
    already satisfies every example of its specification (`verified`) and the test is new → the test. 2026-11-19:
    a fresh test asserted `0.1 > 0.5` after one Q-update with lr=0.1; six repairs of the correct module followed."""
    mod = h.vertices.get(module)
    test_vertex = h.owner_of(test_file)
    test = h.vertices.get(test_vertex) if test_vertex else None
    return mod is not None and mod.state == "verified" and (test is None or test.state != "verified")


def _test_to_review(
    h: Any, module: str, reviewed: set[tuple[str, str]], pending: set[tuple[str, str]] = frozenset()  # type: ignore[assignment]
) -> str | None:
    """A test whose module failed on it at least once and which either never passed (not `verified`) or was written
    against an interface that has since changed (`pending`, set by `_apply_amendment`): its author reviews it once
    per version of the interface before the module is repaired again. After the stubs the harness presumes a test
    correct, so a wrong input (01, 2026-11-22: `act(0)` for a board array) was charged to the module four times.
    `reviewed` holds the pairs already reviewed for the current interface."""
    mod = h.vertices.get(module)
    if mod is None or mod.kind not in ("code", "entry"):
        return None
    # Its own tests first, then any other test the module's failures name: a module is also run by the tests of
    # its callers (2026-11-23, 01: `test_trainer.py` failed inside `agent_qlearn.py` five times).
    candidates = h.tests_of(module) + sorted(v for v, x in h.vertices.items() if x.kind == "test" and v not in h.tests_of(module))
    for test in candidates:
        vertex = h.vertices.get(test)
        if vertex is None or vertex.state == "failed" or (module, test) in reviewed:
            continue
        if vertex.state == "verified" and (module, test) not in pending:
            continue
        name = Path(test).name
        failures = sum(
            1 for entry in mod.history if any(str(i).startswith("Pytest failure") and name in str(i) for i in entry.get("issues", []))
        )
        if failures >= 1:
            return test
    return None
