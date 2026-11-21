"""The import line for a name a module uses undefined, from the one source of truth (D2, 2026-11-14): the canonical
packages and σ of the other planned modules. Only a hint for the author of the file — the harness inserts nothing
(2026-11-21: F821 `np`, `plt`, `pd`, `plot_results` failed six tasks after three repairs each with no hint)."""

from __future__ import annotations

from typing import Any


def importable_names(h: Any, rel: str, packages: dict[str, str]) -> dict[str, str]:
    """`name -> import line` for module `rel`: the canonical `packages` (alias -> import line), `matplotlib` itself,
    every other planned module by its import path, and every top-level public name that exactly one other planned
    module declares in σ. A name with several resolutions has no hint."""
    known = {**packages, "matplotlib": "import matplotlib", "mpl": "import matplotlib as mpl"}
    owners: dict[str, list[str]] = {}
    for edge in (h.edges.values() if h is not None else []):
        if edge.type == "I" and edge.id.removeprefix("I:") != rel and edge.spec.get("import"):
            known.setdefault(edge.spec["import"].split(".")[0], f"import {edge.spec['import']}")
            for symbol in edge.spec.get("symbols", {}):
                if "." not in symbol and not symbol.startswith("_"):
                    owners.setdefault(symbol, []).append(edge.spec["import"])
    known.update({name: f"from {mods[0]} import {name}" for name, mods in owners.items() if len(mods) == 1 and name not in known})
    return known
