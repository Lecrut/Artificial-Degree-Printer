"""Code the workspace already has is its own specification: an existing module the plan imports joins the plan
with its source (brownfield projects)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from adk.hypergraph.model import module_import_path
from adk.orchestration.planning.interfaces import _plan_interfaces


# `import m` / `from m import x`.
_IMPORT_LINE = re.compile(r"^\s*(?:>>>\s*)?(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)


def _with_existing(plan_out: dict[str, Any], existing: dict[str, str] | None) -> dict[str, Any]:
    """The plan with every existing workspace module its interfaces import (transitively) added
    with its own source as its interface: code that is already there is its own specification (2026-11-21, 03: the
    plan imported the baseline `core` without declaring it, and three patches failed on "neither planned nor
    installed")."""
    if not existing:
        return plan_out
    interfaces = dict(_plan_interfaces(plan_out))
    names = {module_import_path(rel): rel for rel in existing} | {Path(rel).stem: rel for rel in existing}
    frontier, added = list(interfaces.values()), False
    while frontier:
        for dotted, plain in _IMPORT_LINE.findall(frontier.pop()):
            rel = names.get(dotted or plain)
            if rel and rel not in interfaces and not Path(rel).name.startswith("test_"):
                interfaces[rel] = existing[rel]
                frontier.append(existing[rel])
                added = True
    return {**plan_out, "interfaces": interfaces} if added else plan_out
