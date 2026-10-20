from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path, write_json_state

LEARNED_HEADER = "## LEARNED RULES AND CONSTRAINTS"


def mutate_agent_prompt(
    agent_md_path: str | Path,
    new_rule: str,
    failure_context: str | None = None,
    failure_ledger_path: str | Path = "state/failure_ledger.json",
) -> dict[str, Any]:
    """Append a learned rule to an agent's .md file (blocking rigid GUARDs) and record in failure_ledger.json."""
    path = resolve_adk_path(agent_md_path)
    if not path.exists():
        raise FileNotFoundError(f"Agent markdown file not found: {agent_md_path}")

    if "guard" in path.stem.lower():
        return {
            "status": "rejected",
            "reason": f"Agent '{path.name}' is a rigid GUARD and cannot be mutated.",
            "file": str(path),
        }

    ledger_file = resolve_adk_path(failure_ledger_path)
    ledger_data = read_json_state(ledger_file) if ledger_file.exists() else {"failures": []}
    ledger_data.setdefault("failures", []).append(
        {
            "agent": path.stem,
            "context": failure_context or "Validation failure in Layer 3",
            "injected_rule": new_rule,
        }
    )
    write_json_state(ledger_file, ledger_data)

    content = path.read_text(encoding="utf-8")
    bullet = f"- **RULE**: {new_rule.strip()}"
    if LEARNED_HEADER in content:
        if bullet not in content:
            updated = content.rstrip() + f"\n{bullet}\n"
        else:
            updated = content
    else:
        updated = content.rstrip() + f"\n\n{LEARNED_HEADER}\n{bullet}\n"

    path.write_text(updated, encoding="utf-8")
    return {
        "status": "mutated",
        "agent": path.stem,
        "file": str(path),
        "injected_rule": new_rule,
    }
