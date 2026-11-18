"""Work from the state of H (Audit VI §VII.12.8): which vertex a task works on, whether it is ready, and the
state a vertex reaches. Pure functions; the orchestrator's scheduler (orchestration/schedule.py) applies them."""

from __future__ import annotations

import re

from adk.hypergraph.model import Hypergraph

# "Chapter 3", "Rozdział 3", and the sections of a chapter ("Section 1.1", "podrozdział 2.3"): 2026-11-17, T1 wrote
# "Section 1.1 (Introduction)", matched no chapter, and chapter 1 stayed `spec` although its task was DONE.
_CHAPTER = re.compile(r"(?:chapter|rozdzia[lł]u?|section|sekcj[ai]|podrozdzia[lł]u?)\s*(\d+)", re.I)
HAS_CONTENT = {"impl", "written", "drafted", "verified"}
CONTENT_STATE = {"code": "impl", "entry": "impl", "test": "written", "chapter": "drafted", "research": "drafted", "bib": "drafted"}


def vertex_of(h: Hypergraph, target: str, description: str = "") -> str | None:
    """The vertex a task works on: its target path, or for `thesis.md` the chapter its description names."""
    target = target.replace("\\", "/")
    if target in h.vertices:
        return target
    if target.endswith("thesis.md"):
        match = _CHAPTER.search(description)
        if match and f"thesis.md#ch{int(match.group(1))}" in h.vertices:
            return f"thesis.md#ch{int(match.group(1))}"
    return None


def readiness(h: Hypergraph, vertex: str, planned: set[str]) -> list[str]:
    """Why `vertex` cannot be worked on yet (empty: it can). A module waits for the modules it uses to have an
    implementation (it is written against their σ, but runs on their code); a test is ready at once (it is checked
    on the stubs); a chapter waits for the results it cites and for planned research it builds on."""
    v = h.vertices[vertex]
    reasons: list[str] = []
    if v.kind in ("code", "entry"):
        for producer in h.edges[f"I:{vertex}"].spec.get("uses", {}):
            if producer in h.vertices and h.vertices[producer].state not in HAS_CONTENT:
                reasons.append(f"{producer} has no implementation yet")
    elif v.kind == "chapter":
        for member, role in h.edges[f"N:{vertex}"].members.items():
            source = h.vertices.get(member)
            if role != "C" or source is None:
                continue
            if source.kind == "data" and source.state != "verified":
                reasons.append(f"{member}: the experiment has not produced current results")
            elif source.kind == "research" and member in planned and source.state not in HAS_CONTENT:
                reasons.append(f"{member} is not written yet")
    return reasons
