"""The project hypergraph — the single record of the project: what it must contain and what it holds (Audit VI
§VII.12, Audit VIII §X)."""

from adk.hypergraph.build import build_from_plan, spec_from_stub
from adk.hypergraph.validate import code_violations
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
