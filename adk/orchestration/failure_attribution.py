"""Who failed: the workspace file and author a pytest failure points to, from its traceback."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_TB_FRAME = re.compile(r"^(\S+?\.py):\d+: in ", re.MULTILINE)
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


def _suspect_test(h: Any, module: str, test_file: str) -> bool:
    """A failed assertion seen only in the test frame blames the unverified one of the pair (§XIV Q2): the module
    already satisfies every example of its specification (`verified`) and the test is new → the test. 2026-11-19:
    a fresh test asserted `0.1 > 0.5` after one Q-update with lr=0.1; six repairs of the correct module followed."""
    mod = h.vertices.get(module)
    test_vertex = h.owner_of(test_file)
    test = h.vertices.get(test_vertex) if test_vertex else None
    return mod is not None and mod.state == "verified" and (test is None or test.state != "verified")
