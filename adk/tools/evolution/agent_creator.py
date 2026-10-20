from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path, write_json_state

ALLOWED_AGENT_DOMAINS = {"building", "verification"}


def create_specialized_agent(
    specialization: str,
    domain: str = "building",
    instructions: str | None = None,
    registry_path: str | Path = "state/agent_registry.json",
    agents_root: str | Path = "agents",
) -> dict[str, Any]:
    """Check agent_registry.json for an active specialization; if absent, create a new .md agent and register it."""
    normalized_domain = (
        "building"
        if domain in ("building", "layer2_builders")
        else ("verification" if domain in ("verification", "layer3_supervisors") else domain)
    )
    if normalized_domain not in ALLOWED_AGENT_DOMAINS:
        raise ValueError(f"Invalid target domain '{domain}'. Expected one of {sorted(ALLOWED_AGENT_DOMAINS)}.")

    a_root = resolve_adk_path(agents_root)
    registry_data = read_json_state(registry_path)
    agents: dict[str, dict[str, Any]] = registry_data.setdefault("agents", {})

    for agent_id, meta in agents.items():
        if meta.get("specialization") == specialization and meta.get("active", True):
            return {
                "status": "exists",
                "agent_id": agent_id,
                "specialization": specialization,
                "domain": normalized_domain,
                "path": meta.get("path"),
            }

    slug = re.sub(r"[^a-z0-9_]+", "_", specialization.lower()).strip("_")
    agent_id = f"dyn_{slug}"
    rel_md_path = f"agents/{normalized_domain}/{agent_id}.md"
    full_md_path = a_root / normalized_domain / f"{agent_id}.md"
    full_md_path.parent.mkdir(parents=True, exist_ok=True)

    body = instructions or (
        f"# ROLE: Dynamic Specialist Agent — `{agent_id}` (`{normalized_domain}` Domain)\n\n"
        f"Specialization: **{specialization}**.\n\n"
        f"## OPERATING RULES\n"
        f"1. Execute only atomic Python tasks assigned to specialization `{specialization}`.\n"
        f"2. Maintain strict consistency with `hypergraph_matrix.json` and symbolic pointers (`\\ref_ast`, `\\ref_csv`).\n"
    )
    full_md_path.write_text(body.strip() + "\n", encoding="utf-8")

    agents[agent_id] = {
        "domain": normalized_domain,
        "path": rel_md_path,
        "specialization": specialization,
        "active": True,
    }
    write_json_state(registry_path, registry_data)

    return {
        "status": "created",
        "agent_id": agent_id,
        "specialization": specialization,
        "domain": normalized_domain,
        "path": rel_md_path,
    }
