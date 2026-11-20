"""The project hypergraph H = (V, E, ρ, σ, Φ, ≺, s): the one record of the project (Audit VI §VII.12, Audit VIII §X).

Vertices are planned artefacts, edges are typed bags of coherence (I interface of one module, R the experiment
run, N one chapter's narrative, S the structure), ρ is the role of a vertex in an edge, σ the edge's specification
and ≺ the order in which edges become checkable. The plan sets the minimum; what the agents add (a helper file, an
import of another planned module, a test of a planned module, a pointer of a chapter) is recorded here too, so H
stays the truth about the workspace. Task targets, verification scope, culprits, agent context and the blast radius
are all computed from H; nothing about the project's structure is kept anywhere else.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

EDGE_TYPES = ("I", "R", "N", "S")
ROLES = ("P", "C", "T", "O", "X")  # producer, consumer/source, test, output, citing chapter
VERTEX_KINDS = ("code", "entry", "test", "data", "figure", "chapter", "bib", "research")


def module_import_path(rel_path: str) -> str:
    """Dotted import path of a workspace module (`src/data/gen.py` -> `src.data.gen`, `src/__init__.py` -> `src`)."""
    parts = Path(rel_path).with_suffix("").parts
    return ".".join(p for p in parts if p != "__init__")


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
    last_writer: dict[str, Any] | None = None  # {agent, task_id} of the last accepted write
    files: list[str] = field(default_factory=list)  # helper files the module owns (imported only through it)
    failures: int = 0  # failed verifications and rejected answers on this vertex in the run (model escalation)


@dataclass
class Edge:
    id: str
    type: str
    members: dict[str, str]  # vertex id -> role
    spec: dict[str, Any] = field(default_factory=dict)
    fingerprint: str | None = None
    observed: list[str] = field(default_factory=list)  # members recorded from the workspace, not planned


@dataclass
class Hypergraph:
    vertices: dict[str, Vertex]
    edges: dict[str, Edge]
    order: list[tuple[str, str]] = field(default_factory=list)  # (earlier, later)

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

    def producer(self, edge: str) -> str | None:
        return next((v for v, role in self.edges[edge].members.items() if role == "P"), None)

    def owner_of(self, rel: str) -> str | None:
        """The vertex a workspace file belongs to: the file's own vertex, or the module owning it as a helper."""
        if rel in self.vertices:
            return rel
        return next((v.id for v in self.vertices.values() if rel in v.files), None)

    def files_of(self, vertex: str) -> list[str]:
        """Workspace files of a vertex: its own path (a chapter lives in thesis.md) and its helper files."""
        v = self.vertices[vertex]
        return [vertex.partition("#")[0], *v.files]

    def tests_of(self, module: str) -> list[str]:
        """Test vertices of a module: the T members of its I bag."""
        edge = self.edges.get(f"I:{module}")
        return sorted(m for m, role in edge.members.items() if role == "T") if edge else []

    def tested_module(self, test: str) -> str | None:
        """The module a test vertex tests (the producer of the I bag it is a T member of)."""
        return next((self.producer(e.id) for e in self.edges.values() if e.type == "I" and e.members.get(test) == "T"), None)

    def output_producer(self, rel: str) -> str | None:
        """The vertex that produces an output (results, figures): the producer of the R bag it is an O member of."""
        return next((self.producer(e.id) for e in self.edges.values() if e.type == "R" and e.members.get(rel) == "O"), None)

    def entry(self) -> str | None:
        """The experiment's entrypoint module."""
        if "R:run" in self.edges:
            return self.producer("R:run")
        return next((v.id for v in self.vertices.values() if v.kind == "entry"), None)

    def plots(self) -> str | None:
        """The module of the plan's declared figures function (`academic_blueprint.plots`), if any."""
        run = self.edges.get("R:run")
        if run is None:
            return None
        return str(run.spec.get("plots") or "").partition(":")[0] or None

    def would_cycle(self, earlier: str, later: str) -> bool:
        """Whether adding `earlier ≺ later` to the order closes a cycle."""
        return earlier == later or earlier in self.later(later)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 2,
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
