"""Offline simulation of the agents and of the literature search, kept apart from the harness.

`install_simulated_agents(task_id)` puts simulated agents behind the harness's model seam (`set_llm_handler`) and an
offline paper catalog behind its literature seam (`set_paper_source`). The harness itself never imports this package
and never branches on whether its agents are real or simulated.

- `scenarios`: per-benchmark fixtures and the first-try mistakes of the simulated agents.
- `agents`: the simulated agents.
- `code_fixtures`, `paper_catalogs`: fixture code, prose and offline literature.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from adk.core.llm import set_llm_handler
from adk.mocks.agents import SimulatedAgents
from adk.mocks.scenarios import SCENARIOS
from adk.tools.building.literature_engine import set_paper_source


def _catalog_source(topic: str, stage: str | None) -> list[dict[str, Any]]:
    from adk.mocks.paper_catalogs import resolve_offline_catalog

    return [dict(p) for p in resolve_offline_catalog(query=topic) if not stage or p.get("stage") == stage]


def install_simulated_agents(task_id: str | None = None, flaws: set[str] | None = None) -> SimulatedAgents:
    """Simulated agents for a benchmark task (its scenario with first-try mistakes) or, by default, well-behaved
    agents on the Tic-Tac-Toe fixtures; plus the offline literature catalog. `flaws` replaces the scenario's
    mistakes (`scenarios.FLAWS`)."""
    scenario = SCENARIOS.get(task_id or "", SCENARIOS["default"])
    if flaws is not None:
        scenario = replace(scenario, flaws=frozenset(flaws))
    agents = SimulatedAgents(scenario)
    set_llm_handler(agents)
    set_paper_source("catalog", _catalog_source)
    return agents


def uninstall_simulated_agents() -> None:
    set_llm_handler(None)
    set_paper_source(None)


__all__ = ["SimulatedAgents", "install_simulated_agents", "uninstall_simulated_agents"]
