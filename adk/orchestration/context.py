"""What an agent is given: the content of its task and the slice of H its vertex's bags determine (Audit VIII §X).

Nothing else about the project goes into a prompt: no exports of every module, no recon metrics, no copy of another
graph. Outside H the agent sees only its own file and the packages of the fixed environment."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state
from adk.hypergraph import Hypergraph
from adk.hypergraph.observe import planned_module_for_test
from adk.tools.building.experiment_runner import EXPERIMENT_TIMEOUT_S


def _spec_view(h: Hypergraph, module: str) -> dict[str, Any]:
    spec = h.edges[f"I:{module}"].spec
    return {k: spec.get(k) for k in ("import", "symbols")}


def _results_targets(workspace: Path, outputs: list[str]) -> tuple[list[str], list[str]]:
    """`file:column` and `file:row` pointer targets of the results files that exist (tidy rows: `method+metric`)."""
    columns: list[str] = []
    rows: list[str] = []
    for rel in outputs:
        path = workspace / rel
        if not path.is_file() or path.suffix != ".csv":
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            reader = list(csv.DictReader(handle))
        cols = list(reader[0].keys()) if reader else []
        columns += [f"{rel}:{c}" for c in cols]
        if {"method", "metric"} <= set(cols):
            rows += [f"{rel}:{r['method']}+{r['metric']}" for r in reader if r.get("method") and r.get("metric")]
        elif cols:
            rows += [f"{rel}:{r[cols[0]]}" for r in reader if r.get(cols[0])]
    return list(dict.fromkeys(columns)), list(dict.fromkeys(rows))


class ContextMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _context_for(self, vertex: str | None, node_path: str) -> dict[str, Any]:
        """The H slice of one task: σ of the module and of what it uses, its tests and history (code); σ of the
        module under test (test); the chapter's plan and every pointer target it may cite (chapter)."""
        h = self._project_h()
        if h is None:
            return {}
        vertex = vertex or h.owner_of(node_path)
        if vertex is None and Path(node_path).name.startswith("test_"):
            module = planned_module_for_test(h, node_path)  # a test file the plan did not name
            return {"specification": {module: _spec_view(h, module)}} if module else {}
        if vertex is None:
            return self._document_context_slice(h) if node_path.endswith((".md", ".tex")) else {}
        v = h.vertices[vertex]
        context: dict[str, Any] = {}
        if v.kind in ("code", "entry", "test"):
            own = [e.id.removeprefix("I:") for e in h.edges.values() if e.type == "I" and vertex in e.members]
            relevant = set(own) | {p for rel in own for p in h.edges[f"I:{rel}"].spec.get("uses", {})}
            context["specification"] = {rel: _spec_view(h, rel) for rel in sorted(relevant) if f"I:{rel}" in h.edges}
            if v.kind != "test":
                context["tested_by"] = h.tests_of(vertex)
            run = h.edges.get("R:run")
            if run is not None and run.members.get(vertex) in ("P", "C"):
                context["experiment"] = {
                    "entrypoint": run.spec.get("entry"),
                    "metrics": run.spec.get("metrics", []),
                    "results": sorted(m for m, role in run.members.items() if role == "O"),
                    "plots": run.spec.get("plots") or None,
                    "time_limit_s": EXPERIMENT_TIMEOUT_S,
                }
        elif v.kind == "chapter":
            context.update(self._document_context_slice(h))
            context["chapter"] = h.edges[f"N:{vertex}"].spec
        elif v.kind in ("research", "bib"):
            context.update(self._literature_slice())
        if v.history:
            context["previous_attempts"] = list(v.history)
        return context

    def _h_slice(self, vertex: str | None) -> dict[str, Any]:
        """The bags of one vertex for a planner: members with their roles, σ, and the state of every member."""
        h = self._project_h()
        if h is None or vertex is None or vertex not in h.vertices:
            return {}
        bags: dict[str, Any] = {}
        for edge_id in sorted(h.edges_of(vertex)):
            edge = h.edges[edge_id]
            spec = {k: v for k, v in edge.spec.items() if k in ("import", "symbols", "entry", "metrics", "title", "focus")}
            bags[edge_id] = {
                "members": {m: {"role": role, "state": h.vertices[m].state if m in h.vertices else None} for m, role in edge.members.items()},
                "spec": spec,
            }
        return {"vertex": vertex, "kind": h.vertices[vertex].kind, "state": h.vertices[vertex].state, "bags": bags}

    def _literature_slice(self) -> dict[str, Any]:
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        recon = blueprint.get("literature_recon", {}) if isinstance(blueprint, dict) else {}
        return {
            "thesis_type": blueprint.get("thesis_type", "inzynierska"),
            "available_citation_keys": list((recon or {}).get("available_citation_keys") or []),
        }

    def _document_context_slice(self, h: Hypergraph) -> dict[str, Any]:
        """Everything a chapter may cite, all of it from H: the public symbols of the planned modules (σ), the
        rows and columns of the results the experiment wrote, the figures on disk, the verified citation keys."""
        symbols = [
            f"{e.id.removeprefix('I:')}:{name}"
            for e in h.edges.values()
            if e.type == "I"
            for name, sym in e.spec.get("symbols", {}).items()
            if sym.get("kind") in ("const", "func", "class")
        ]
        outputs = sorted({m for e in h.edges.values() if e.type == "R" for m, role in e.members.items() if role == "O"})
        columns, rows = _results_targets(self.workspace_dir, outputs)
        figures = sorted(
            p.relative_to(self.workspace_dir).as_posix()
            for p in (self.workspace_dir.rglob("*") if self.workspace_dir.exists() else [])
            if p.is_file() and p.suffix.lower() in (".pdf", ".png", ".svg") and "figures" in p.parts
        )
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        chapters = [e.spec for e in h.edges.values() if e.type == "N"]
        return {
            "may_cite": {
                "available_ast_symbols": symbols,
                "available_csv_columns": columns,
                "available_csv_rows": rows,
                "available_figures": figures,
            },
            "planned_chapters": [{"title": c.get("title"), "focus": c.get("focus")} for c in chapters],
            "template_name": blueprint.get("template_name", "thesis_plodz"),
            **self._literature_slice(),
        }
