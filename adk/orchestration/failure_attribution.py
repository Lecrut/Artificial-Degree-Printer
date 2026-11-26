"""Who failed: the workspace file and author a pytest failure points to, from its traceback."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_TB_FRAME = re.compile(r"^(\S+?\.py):\d+: in ", re.MULTILINE)
_HANG_FRAME = re.compile(r'^File "([^"]+?\.py)", line (?:\d+|\?+) in ', re.MULTILINE)
_TB_EXC = re.compile(r"^E\s+([A-Za-z_][\w.]*)", re.MULTILINE)
# What surfaces only in the test frame and is a wrong result of the code under test: a failed assertion (pytest
# prints `E   assert a == b` for it, so its "exception" reads `assert`). Every other exception raised in the
# test's own code (`ValueError` of `array in [...]`, `IndexError` of the test's own data, a misused API) is the
# test's (2026-11-25, 01: `state1 in [tuple(s) ...]` raised `ValueError` in the test frame and six repairs of the
# correct `q_learning_agent.py` followed).
_WRONG_RESULT = {"AssertionError", "Failed", "assert", ""}


def _is_test(rel: str) -> bool:
    name = Path(rel).name
    return rel.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def _pytest_culprits(issue: str) -> list[tuple[str, bool]]:
    """Per failed test in a `--tb=short` pytest report: (deepest workspace frame, whether that is the code under
    test). A frame below the test means the code raised; only the test frame means either the test misuses the
    API (an exception other than a failed assertion, culprit = test) or the code returned a wrong value (assertion, culprit = code; the
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
        found.append((frames[0], exc in _WRONG_RESULT))
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
    a fresh test asserted `0.1 > 0.5` after one Q-update with lr=0.1; six repairs of the correct module followed.
    A module that never passed is also cleared once the same error of the same test survives two different
    versions of it (§XXX P6: `R1_2`-`R6_1` rewrote `q_learning_agent.py` six times for a test that fed it `[0.5, 0.0]`)."""
    mod = h.vertices.get(module)
    test_vertex = h.owner_of(test_file)
    test = h.vertices.get(test_vertex) if test_vertex else None
    if mod is None or (test is not None and test.state == "verified"):
        return False
    return mod.state == "verified" or _error_survives_rewrites(mod.history, test_file)


_E_LINE = re.compile(r"^E\s+(\S.*)$", re.MULTILINE)
REWRITES_BEFORE_TEST_IS_SUSPECT = 2


def _error_survives_rewrites(history: list[dict[str, Any]], test_file: str) -> bool:
    """The module's remembered verdicts show the same `E ...` lines of `test_file` under at least
    `REWRITES_BEFORE_TEST_IS_SUSPECT` different versions of the module file (`version` of each entry)."""
    name = Path(test_file).name
    versions: dict[frozenset[str], set[str]] = {}
    for entry in history:
        version = str(entry.get("version") or "")
        for issue in entry.get("issues", []):
            text = str(issue)
            if text.startswith("Pytest failure") and name in text and (lines := frozenset(m.strip() for m in _E_LINE.findall(text))):
                versions.setdefault(lines, set()).add(version)
    return any(len(v - {""}) >= REWRITES_BEFORE_TEST_IS_SUSPECT for v in versions.values())


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
        # A `failed` test is reviewed too: in 01 R2_2 `test_env_step_draw_condition` used moves [0..8] (X wins on
        # 0-4-8, not a draw) alongside `environment.py` missing `self.current_player = next_player` (§XXVII).
        if vertex is None or (module, test) in reviewed:
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
