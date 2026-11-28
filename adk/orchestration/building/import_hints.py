"""The import line for a name a module uses undefined, from the one source of truth (D2, 2026-11-14): the canonical
packages and σ of the other planned modules. Only a hint for the author of the file — the harness inserts nothing
(2026-11-21: F821 `np`, `plt`, `pd`, `plot_results` failed six tasks after three repairs each with no hint)."""

from __future__ import annotations

from typing import Any

# Annotation names every module may use; `typing` is not in the canonical packages (§XXXVI: 01, 2026-11-26,
# `experiment.py` used `Dict`, `List` and `Any` undefined in three repairs, none of them with an import hint).
TYPING_NAMES = (
    "Any", "Callable", "Dict", "Iterable", "List", "Literal", "Mapping", "Optional", "Sequence", "Set", "Tuple", "Union",
)


def importable_names(h: Any, rel: str, packages: dict[str, str]) -> dict[str, str]:
    """`name -> import line` for module `rel`: the canonical `packages` (alias -> import line), `matplotlib` itself,
    every other planned module by its import path, and every top-level public name that exactly one other planned
    module declares in σ. A name with several resolutions has no hint."""
    known = {**{n: f"from typing import {n}" for n in TYPING_NAMES}, **packages, "matplotlib": "import matplotlib", "mpl": "import matplotlib as mpl"}
    owners: dict[str, list[str]] = {}
    for edge in (h.edges.values() if h is not None else []):
        if edge.type == "I" and edge.id.removeprefix("I:") != rel and edge.spec.get("import"):
            known.setdefault(edge.spec["import"].split(".")[0], f"import {edge.spec['import']}")
            for symbol in edge.spec.get("symbols", {}):
                if "." not in symbol and not symbol.startswith("_"):
                    owners.setdefault(symbol, []).append(edge.spec["import"])
    known.update({name: f"from {mods[0]} import {name}" for name, mods in owners.items() if len(mods) == 1 and name not in known})
    # What σ of this very module says it uses from other modules settles an otherwise ambiguous name (U5, §XXII).
    own = h.edges.get(f"I:{rel}") if h is not None else None
    for producer, names in (own.spec.get("uses", {}) if own is not None else {}).items():
        edge = h.edges.get(f"I:{producer}")
        if edge is not None and edge.spec.get("import"):
            known.update({name: f"from {edge.spec['import']} import {name}" for name in names if name != "*"})
    return known


def own_declarations(h: Any, rel: str) -> dict[str, str]:
    """`name -> declaration` of the top-level constants the planned interface of `rel` itself declares: an undefined
    one was dropped when the file was rewritten (02, 2026-11-22: `N_ESTIMATORS`, `SUBSPACE_DIMENSION` lost in three
    rewrites of the same file)."""
    edge = h.edges.get(f"I:{rel}") if h is not None else None
    return {
        name: f"{name}: {sym['type']}" if sym.get("type") else name
        for name, sym in (edge.spec.get("symbols", {}) if edge is not None else {}).items()
        if sym.get("kind") == "const" and "." not in name
    }
