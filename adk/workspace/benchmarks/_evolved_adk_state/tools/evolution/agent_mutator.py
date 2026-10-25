from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.llm import call_agent
from adk.core.models import read_json_state, resolve_adk_path, write_json_state

LEARNED_HEADER = "## LEARNED RULES AND CONSTRAINTS"
CONSOLIDATED_HEADER = "## CONSOLIDATED EVOLUTIONARY INVARIANTS"
DEFAULT_COMPACTION_THRESHOLD = 4


def _extract_raw_rules(learned_section: str) -> list[str]:
    """Extract all raw '- **RULE**: ...' entries from the LEARNED RULES section."""
    rules: list[str] = []
    for line in learned_section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- **RULE**:"):
            rules.append(stripped.removeprefix("- **RULE**:").strip())
    return rules


def _extract_existing_invariants(base_prompt: str) -> list[str]:
    """Extract existing '- **INVARIANT**: ...' entries from the CONSOLIDATED section."""
    if CONSOLIDATED_HEADER not in base_prompt:
        return []
    after_header = base_prompt.split(CONSOLIDATED_HEADER, 1)[1]
    invariants: list[str] = []
    for line in after_header.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("- **INVARIANT"):
            invariants.append(stripped)
    return invariants


def consolidate_agent_prompt(
    agent_md_path: str | Path,
    failure_ledger_path: str | Path = "state/failure_ledger.json",
    provider: str | None = None,
) -> dict[str, Any]:
    """Perform a full redaction/consolidation of an agent's .md prompt when accumulated rules reach the threshold."""
    path = resolve_adk_path(agent_md_path)
    if not path.exists():
        raise FileNotFoundError(f"Agent markdown file not found: {agent_md_path}")

    if "guard" in path.stem.lower():
        return {
            "status": "rejected",
            "reason": f"Agent '{path.name}' is a rigid GUARD and cannot be redacted.",
            "file": str(path),
        }

    content = path.read_text(encoding="utf-8")
    if LEARNED_HEADER in content:
        base_part, learned_part = content.split(LEARNED_HEADER, 1)
    else:
        base_part, learned_part = content, ""

    raw_rules = _extract_raw_rules(learned_part)
    if not raw_rules:
        return {
            "status": "no_op",
            "agent": path.stem,
            "file": str(path),
            "rules_consolidated": 0,
        }

    existing_invariants = _extract_existing_invariants(base_part)
    consolidator_md = resolve_adk_path("agents/evolution/prompt_consolidator.md")

    consolidated_invariant = " | ".join(dict.fromkeys(raw_rules))
    redacted_base: str | None = None

    if consolidator_md.exists():
        llm_res = call_agent(
            consolidator_md,
            {
                "agent_id": path.stem,
                "base_prompt": base_part.strip(),
                "accumulated_rules": raw_rules,
                "existing_consolidated_invariants": existing_invariants,
            },
            model_tier="LRM",
            provider=provider,
        )["output"]
        if isinstance(llm_res, dict):
            if llm_res.get("consolidated_invariant"):
                consolidated_invariant = str(llm_res["consolidated_invariant"]).strip()
            candidate_base = llm_res.get("redacted_base_prompt")
            if (
                isinstance(candidate_base, str)
                and "REQUIRED JSON OUTPUT SCHEMA" in candidate_base
                and "# ROLE" in candidate_base
            ):
                redacted_base = candidate_base.strip()

    effective_base = redacted_base if redacted_base is not None else base_part.rstrip()
    cycle_num = len(existing_invariants) + 1
    invariant_bullet = f"- **INVARIANT (Cycle {cycle_num})**: {consolidated_invariant}"

    if CONSOLIDATED_HEADER in effective_base:
        effective_base = effective_base.rstrip() + f"\n{invariant_bullet}"
    else:
        effective_base = effective_base.rstrip() + f"\n\n---\n\n{CONSOLIDATED_HEADER}\n{invariant_bullet}"

    # Preserve previous epoch notes if any, but clear all raw '- **RULE**:' entries
    epoch_lines = [
        line.strip()
        for line in learned_part.splitlines()
        if line.strip().startswith("- **CONSOLIDATED_EPOCH")
    ]
    epoch_lines.append(
        f"- **CONSOLIDATED_EPOCH {cycle_num}**: Redacted and consolidated {len(raw_rules)} rules into the invariants section."
    )

    learned_rebuilt = "\n".join(epoch_lines)

    new_full_content = f"{effective_base.rstrip()}\n\n{LEARNED_HEADER}\n{learned_rebuilt}\n"
    path.write_text(new_full_content, encoding="utf-8")

    ledger_file = resolve_adk_path(failure_ledger_path)
    ledger_data = read_json_state(ledger_file) if ledger_file.exists() else {"failures": []}
    ledger_data.setdefault("compactions", []).append(
        {
            "agent": path.stem,
            "cycle": cycle_num,
            "rules_consolidated_count": len(raw_rules),
            "consolidated_rules": raw_rules,
            "synthesized_invariant": consolidated_invariant,
        }
    )
    write_json_state(ledger_file, ledger_data)

    return {
        "status": "consolidated",
        "agent": path.stem,
        "file": str(path),
        "cycle": cycle_num,
        "rules_consolidated": len(raw_rules),
        "consolidated_invariant": consolidated_invariant,
    }


def mutate_agent_prompt(
    agent_md_path: str | Path,
    new_rule: str,
    failure_context: str | None = None,
    failure_ledger_path: str | Path = "state/failure_ledger.json",
    compaction_threshold: int = DEFAULT_COMPACTION_THRESHOLD,
    provider: str | None = None,
) -> dict[str, Any]:
    """Append a learned rule to an agent's .md file (blocking rigid GUARDs) and auto-redact every `compaction_threshold` (4) rules."""
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

    # Count accumulated raw rules under LEARNED_HEADER; trigger full prompt redaction every `compaction_threshold` (default 4) rules
    _, learned_section = updated.split(LEARNED_HEADER, 1)
    active_raw_rules = _extract_raw_rules(learned_section)
    compaction_result: dict[str, Any] | None = None
    if compaction_threshold > 0 and len(active_raw_rules) >= compaction_threshold:
        compaction_result = consolidate_agent_prompt(
            agent_md_path=path,
            failure_ledger_path=ledger_file,
            provider=provider,
        )

    return {
        "status": "mutated",
        "agent": path.stem,
        "file": str(path),
        "injected_rule": new_rule,
        "active_rules_count": 0 if compaction_result else len(active_raw_rules),
        "compacted": compaction_result is not None,
        "compaction_details": compaction_result,
    }
