"""The project hypergraph H = (V, E, ρ, σ, Φ, ≺, s): the one record of what the project must contain (Audit VI §VII.12).

Vertices are planned artefacts, edges are typed bags of coherence (I interface of one module, R the experiment
run, N one chapter's narrative, S the structure), ρ is the role of a vertex in an edge, σ the edge's specification
and ≺ the order in which edges become checkable. The incidence matrix, d(v) and the blast radius are computed,
never stored next to the edges (the old `hypergraph_matrix.json` kept `edges`, `matrix` and `degree` side by side).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

EDGE_TYPES = ("I", "R", "N", "S")
ROLES = ("P", "C", "T", "O", "X")  # producer, consumer/source, test, output, citing chapter
VERTEX_KINDS = ("code", "entry", "test", "data", "figure", "chapter", "bib", "research")
INITIAL_STATE = {"code": "stub", "entry": "stub"}  # every other kind starts at "spec"


@dataclass
class Violation:
    """A breach of an invariant or of σ: `rule` is a stable code, `culprit` the vertex that must change."""

    rule: str
    detail: str
    vertex: str | None = None
    culprit: str | None = None

    def __str__(self) -> str:
        where = f" [{self.vertex}]" if self.vertex else ""
        return f"{self.rule}{where}: {self.detail}"


@dataclass
class Vertex:
    id: str
    kind: str
    owner: str | None
    state: str = "spec"
    description: str = ""
    attempts: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Edge:
    id: str
    type: str
    members: dict[str, str]  # vertex id -> role
    spec: dict[str, Any] = field(default_factory=dict)
    fingerprint: str | None = None


@dataclass
class Hypergraph:
    vertices: dict[str, Vertex]
    edges: dict[str, Edge]
    order: list[tuple[str, str]] = field(default_factory=list)  # (earlier, later)
    built_from_plan: str = ""

    def edges_of(self, vertex: str) -> list[str]:
        return [e.id for e in self.edges.values() if vertex in e.members]

    def degree(self, vertex: str) -> int:
        """d(v): number of I/R/N bags the vertex belongs to (S contains everything and is not counted)."""
        return sum(1 for e in self.edges.values() if e.type != "S" and vertex in e.members)

    def incidence(self) -> dict[str, dict[str, str]]:
        """ρ as a matrix: vertex -> edge -> role (absent = not a member)."""
        return {v: {e.id: e.members[v] for e in self.edges.values() if v in e.members} for v in self.vertices}

    def later(self, edge: str) -> set[str]:
        """Every edge after `edge` in ≺ (transitive)."""
        found: set[str] = set()
        frontier = [edge]
        while frontier:
            current = frontier.pop()
            for earlier, after in self.order:
                if earlier == current and after not in found:
                    found.add(after)
                    frontier.append(after)
        return found

    def blast_radius(self, vertex: str) -> set[str]:
        """Edges to re-check after `vertex` changed: its own bags and everything after them in ≺."""
        own = set(self.edges_of(vertex))
        return own.union(*(self.later(e) for e in own)) if own else set()

    def producer(self, edge: str) -> str | None:
        return next((v for v, role in self.edges[edge].members.items() if role == "P"), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 2,
            "built_from_plan": self.built_from_plan,
            "vertices": {k: {kk: vv for kk, vv in asdict(v).items() if kk != "id"} for k, v in self.vertices.items()},
            "edges": {k: {kk: vv for kk, vv in asdict(e).items() if kk != "id"} for k, e in self.edges.items()},
            "order": [list(pair) for pair in self.order],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hypergraph:
        return cls(
            vertices={k: Vertex(id=k, **v) for k, v in data.get("vertices", {}).items()},
            edges={k: Edge(id=k, **e) for k, e in data.get("edges", {}).items()},
            order=[(a, b) for a, b in data.get("order", [])],
            built_from_plan=str(data.get("built_from_plan", "")),
        )


def save(h: Hypergraph, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(h.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load(path: str | Path) -> Hypergraph | None:
    p = Path(path)
    return Hypergraph.from_dict(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None


def _has_cycle(order: list[tuple[str, str]]) -> list[str]:
    graph: dict[str, list[str]] = {}
    for a, b in order:
        graph.setdefault(a, []).append(b)
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        state[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                return stack[stack.index(nxt):] + [nxt]
            if state.get(nxt) is None and (cycle := visit(nxt)):
                return cycle
        state[node] = 2
        stack.pop()
        return []

    for node in list(graph):
        if state.get(node) is None and (cycle := visit(node)):
            return cycle
    return []


def check_invariants(h: Hypergraph) -> list[Violation]:
    """Invariants of §VII.12.10 that need only H (stub imports and packages are checked by `build`)."""
    found: list[Violation] = []
    for v in h.vertices.values():
        if v.kind not in VERTEX_KINDS:
            found.append(Violation("UNKNOWN_KIND", f"kind {v.kind!r}", v.id))
        if not any(e.type != "S" and v.id in e.members for e in h.edges.values()):
            found.append(Violation("ORPHAN_VERTEX", "belongs to no I, R or N bag", v.id))
    produced: dict[str, list[str]] = {}
    for e in h.edges.values():
        if e.type not in EDGE_TYPES:
            found.append(Violation("UNKNOWN_EDGE_TYPE", f"type {e.type!r}", e.id))
        for member, role in e.members.items():
            if member not in h.vertices:
                found.append(Violation("UNKNOWN_MEMBER", f"{member} is not a vertex", e.id))
            if role not in ROLES:
                found.append(Violation("UNKNOWN_ROLE", f"{member}: {role!r}", e.id))
        producers = [m for m, r in e.members.items() if r == "P"]
        if e.type in ("I", "R") and len(producers) != 1:
            found.append(Violation("PRODUCER_COUNT", f"{len(producers)} producers, expected 1", e.id))
        if e.type == "I":
            for p in producers:
                produced.setdefault(p, []).append(e.id)
    for v in h.vertices.values():
        if v.kind in ("code", "entry") and len(produced.get(v.id, [])) != 1:
            found.append(Violation("MODULE_WITHOUT_ONE_INTERFACE", f"producer of {produced.get(v.id, [])}", v.id))
    runs = [e for e in h.edges.values() if e.type == "R"]
    if len(runs) > 1:
        found.append(Violation("RUN_COUNT", f"{len(runs)} R bags, expected at most 1"))
    for a, b in h.order:
        if a not in h.edges or b not in h.edges:
            found.append(Violation("ORDER_UNKNOWN_EDGE", f"{a} ≺ {b}"))
    if cycle := _has_cycle(h.order):
        found.append(Violation("ORDER_CYCLE", " ≺ ".join(cycle)))
    return found
