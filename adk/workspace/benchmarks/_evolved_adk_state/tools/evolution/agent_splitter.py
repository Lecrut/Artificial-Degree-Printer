from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path, write_json_state


def split_agent(
    agent_id: str,
    sub_specializations: list[str] | tuple[str, str] = ("unit_testing", "edge_case_testing"),
    registry_path: str | Path = "state/agent_registry.json",
    agents_root: str | Path = "agents",
) -> dict[str, Any]:
    """Archive an overly broad agent and split it into two narrower specialized .md agents."""
    if len(sub_specializations) != 2:
        raise ValueError("split_agent requires exactly two target sub_specializations.")

    a_root = resolve_adk_path(agents_root)
    registry_data = read_json_state(registry_path)
    agents: dict[str, dict[str, Any]] = registry_data.setdefault("agents", {})

    if agent_id not in agents:
        raise KeyError(f"Agent '{agent_id}' not found in agent_registry.json.")

    if "guard" in agent_id.lower():
        raise PermissionError(f"Rigid GUARD agent '{agent_id}' cannot be split.")

    parent_meta = agents[agent_id]
    domain = parent_meta.get("domain", "building")
    parent_rel_path = parent_meta.get("path", f"agents/{domain}/{agent_id}.md")
    parent_full_path = a_root.parent / parent_rel_path if not (a_root / parent_rel_path).exists() else (a_root / parent_rel_path)

    inherited_tail = (
        "## CONSOLIDATED EVOLUTIONARY INVARIANTS\n"
        f"- **INVARIANT (Inherited from `{agent_id}`)**: Maintain strict determinism, AST validity, and CSV artifact freshness.\n\n"
        "## LEARNED RULES AND CONSTRAINTS\n"
    )
    if parent_full_path.exists():
        parent_text = parent_full_path.read_text(encoding="utf-8")
        if "## CONSOLIDATED EVOLUTIONARY INVARIANTS" in parent_text:
            inherited_tail = "## CONSOLIDATED EVOLUTIONARY INVARIANTS" + parent_text.split(
                "## CONSOLIDATED EVOLUTIONARY INVARIANTS", 1
            )[1]
        elif "## LEARNED RULES AND CONSTRAINTS" in parent_text:
            inherited_tail = (
                "## CONSOLIDATED EVOLUTIONARY INVARIANTS\n"
                f"- **INVARIANT (Inherited from `{agent_id}`)**: Maintain strict determinism and AST validity.\n\n"
                "## LEARNED RULES AND CONSTRAINTS"
                + parent_text.split("## LEARNED RULES AND CONSTRAINTS", 1)[1]
            )


    parent_meta["active"] = False
    parent_meta["archived_reason"] = f"Split into {sub_specializations[0]} and {sub_specializations[1]}"

    created_agents: list[str] = []
    for spec in sub_specializations:
        slug = re.sub(r"[^a-z0-9_]+", "_", spec.lower()).strip("_")
        child_id = f"{agent_id}_{slug}"
        rel_path = f"agents/{domain}/{child_id}.md"
        full_path = a_root / domain / f"{child_id}.md"
        full_path.parent.mkdir(parents=True, exist_ok=True)

        md_content = (
            f"# ROLE: Specialized Sub-Agent `{child_id}` (split from `{agent_id}` — `{domain}` Domain)\n\n"
            f"You are a focused specialist sub-agent (`{child_id}`) created by splitting `{agent_id}` in the **Artificial-Degree-Printer**.\n"
            f"Narrow Specialization: **{spec}**.\n\n"
            f"---\n\n"
            f"## 1. SCOPE OF RESPONSIBILITY\n"
            f"1. Focus exclusively on atomic tasks within the `{spec}` specialization.\n"
            f"2. Enforce strict Python 3.12+ AST syntax validity, deterministic execution, and hypergraph consistency.\n"
            f"3. Preserve symbolic grounding (`\\ref_ast{{file:symbol}}`, `\\ref_csv{{file:row:column}}`) and artifact freshness (`mtime`).\n\n"
            f"---\n\n"
            f"## 2. REQUIRED JSON OUTPUT SCHEMA\n"
            f"Return strictly a valid JSON object matching this schema:\n"
            f"```json\n"
            f"{{\n"
            f'  "ast_edits": [],\n'
            f'  "test_file": "test_core.py",\n'
            f'  "test_code": "def test_{slug}():\\n    assert True\\n",\n'
            f'  "benchmark_file": "results.csv",\n'
            f'  "csv_content": "",\n'
            f'  "summary": "Executed specialized {spec} task."\n'
            f"}}\n"
            f"```\n"
            f"Do not output conversational text or markdown wrappers outside the JSON.\n\n"
            f"---\n\n"
            f"{inherited_tail.strip()}\n"
        )
        full_path.write_text(md_content, encoding="utf-8")

        agents[child_id] = {
            "domain": domain,
            "path": rel_path,
            "specialization": spec,
            "parent_agent": agent_id,
            "active": True,
        }
        created_agents.append(child_id)

    write_json_state(registry_path, registry_data)
    return {
        "status": "split",
        "archived_agent": agent_id,
        "created_agents": created_agents,
    }
