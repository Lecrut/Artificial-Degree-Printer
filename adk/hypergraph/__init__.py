"""The project hypergraph — the single record of what the project must contain (Audit VI §VII.12)."""

from adk.hypergraph.build import build_from_plan, code_violations, spec_from_stub
from adk.hypergraph.model import Edge, Hypergraph, Vertex, Violation, check_invariants, load, save
from adk.hypergraph.observe import diff, observe

__all__ = [
    "Edge",
    "Hypergraph",
    "Vertex",
    "Violation",
    "build_from_plan",
    "check_invariants",
    "code_violations",
    "diff",
    "load",
    "observe",
    "save",
    "spec_from_stub",
]
