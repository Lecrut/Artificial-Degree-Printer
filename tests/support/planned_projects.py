"""A mock plan as a test needs it: the specification of the default scenario and an orchestrator that has the hypergraph a planned run would have."""

from __future__ import annotations

import json
from typing import Any

from adk.hypergraph import Hypergraph, build_from_plan, save
from adk.mocks.scenarios import ENTRYPOINT, SCENARIOS

SPEC = {"interfaces": SCENARIOS["default"].interfaces(), "entrypoint": ENTRYPOINT, "plots": "plot_results.py:generate_plots"}


def with_plan(
    orch: Any,
    interfaces: dict[str, str],
    entrypoint: str | None = None,
    tasks: list[dict[str, Any]] | None = None,
    chapters: list[dict[str, Any]] | None = None,
    metrics: list[str] | None = None,
    plots: str | None = None,
) -> Hypergraph:
    """Write the blueprint and build H from `interfaces` for `orch`, as planning does (stubs are not written)."""
    blueprint = {"interfaces": interfaces, "entrypoint": entrypoint or "", "planned_chapters": chapters or [], "metrics": metrics or [], "plots": plots or ""}
    orch.blueprint_path.write_text(json.dumps(blueprint), encoding="utf-8")
    h, _problems = build_from_plan(interfaces, entrypoint, tasks or [], chapters or [], metrics or [], plots)
    save(h, orch.hypergraph_path)
    orch.hypergraph = h
    return h
