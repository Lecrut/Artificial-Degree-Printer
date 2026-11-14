from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from adk.core.llm import call_agent
from adk.core.models import read_json_state, resolve_adk_path, write_json_state

LEARNED_HEADER = "## LEARNED RULES AND CONSTRAINTS"
CONSOLIDATED_HEADER = "## CONSOLIDATED EVOLUTIONARY INVARIANTS"
DEFAULT_COMPACTION_THRESHOLD = 4
# The learned section is read on every call of the agent; it stays small or it stops being read (§IV.6.3 C).
MAX_INVARIANTS = 6
MAX_INVARIANTS_CHARS = 1200
# A rule that did not lower the frequency of its failure category is noise; it needs this many cycles of
# evidence after it was written before that judgement is made (§IV.6.3 D).
MIN_CYCLES_AFTER_RULE = 3

# A rule that encodes a symptom (an error code, an exception type, a line number) instead of a way of working.
_SYMPTOM = re.compile(
    r"\b[A-Z]{1,4}\d{3,4}\b|\b(?:Syntax|Indentation|Name|Import|Attribute|Type|Module(?:NotFound)?)Error\b"
    r"|\bline\s+\d+\b|\blini[aie]\s+\d+\b"
)
# What the harness enforces itself: syntax, answer shape, import resolution. A prompt rule adds nothing here.
_HARNESS_TOPICS = re.compile(
    r"(?i)\b(?:docstring|triple[- ]?quot\w*|potrójn\w*|cudzysł\w*|indent\w*|wcięc\w*|parenthes\w*|bracket\w*|nawias\w*"
    r"|sys\.path|'files'|\"files\"|src\.\s*prefix|prefiks\w*\s+src)"
)


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-ząćęłńóśźż]{3,}", text.lower())}


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def rule_rejection_reason(rule: str, forbidden_names: set[str], existing_rules: list[str]) -> str | None:
    """Why a proposed learned rule must not enter a prompt, or None when it may (§IV.6.3 B).

    Rejected: a rule naming a file or symbol of this project, a rule encoding a symptom, a rule about something
    the harness enforces, and a near-duplicate of a rule the agent already has."""
    words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", rule))
    named = sorted(w for w in words if w in forbidden_names or w.split(".")[0] in forbidden_names)
    if named:
        return f"nazywa konkretne pliki/symbole projektu: {', '.join(named[:5])}"
    if _SYMPTOM.search(rule):
        return "koduje objaw (kod błędu, typ wyjątku, numer linii) zamiast metody pracy"
    if _HARNESS_TOPICS.search(rule):
        return "dotyczy tego, co egzekwuje harness (składnia, kształt odpowiedzi, importy)"
    for old in existing_rules:
        if _similarity(rule, old) >= 0.6:
            return f"powtarza istniejącą regułę: {old[:80]}"
    return None


def _extract_raw_rules(learned_section: str) -> list[str]:
    """Extract all raw '- **RULE**: ...' entries from the LEARNED RULES section."""
    rules: list[str] = []
    for line in learned_section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- **RULE**:"):
            rules.append(stripped.removeprefix("- **RULE**:").strip())
    return rules


def _extract_existing_invariants(base_prompt: str) -> list[str]:
    """Texts of the '- **INVARIANT ...**: ...' entries of the CONSOLIDATED section (without the bullet prefix)."""
    if CONSOLIDATED_HEADER not in base_prompt:
        return []
    after_header = base_prompt.split(CONSOLIDATED_HEADER, 1)[1]
    invariants: list[str] = []
    for line in after_header.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("- **INVARIANT"):
            invariants.append(stripped.split("**:", 1)[-1].strip())
    return invariants


def learned_rules_of(agent_md_path: Path) -> list[str]:
    """Every learned rule and invariant an agent's prompt currently carries."""
    if not agent_md_path.exists():
        return []
    content = agent_md_path.read_text(encoding="utf-8")
    base, _, learned = content.partition(LEARNED_HEADER)
    return _extract_existing_invariants(base) + _extract_raw_rules(learned)


def _effective_rules(raw_rules: list[str], ledger: dict[str, Any], agent: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Split rules into those worth keeping and those whose failure category did not get rarer after them.
    Uses `ledger.rules` (rule -> category, cycle) and `ledger.category_log` (every failure with its cycle)."""
    records = {r.get("rule"): r for r in ledger.get("rules", []) if r.get("agent") == agent}
    log = [e for e in ledger.get("category_log", []) if e.get("agent") == agent]
    current = max((int(e.get("cycle", 0)) for e in log), default=0)
    kept: list[str] = []
    dropped: list[dict[str, Any]] = []
    for rule in raw_rules:
        rec = records.get(rule) or {}
        category, cycle = str(rec.get("category") or ""), int(rec.get("cycle") or 0)
        window = current - cycle
        if not category or cycle <= 0 or window < MIN_CYCLES_AFTER_RULE:
            kept.append(rule)
            continue
        same = [e for e in log if e.get("category") == category]
        before = sum(1 for e in same if int(e.get("cycle", 0)) <= cycle)
        after = sum(1 for e in same if int(e.get("cycle", 0)) > cycle)
        if after and after / window >= before / cycle:
            dropped.append({"rule": rule, "category": category, "before": before, "after": after, "cycles_after": window})
        else:
            kept.append(rule)
    return kept, dropped


def _fit_invariants(invariants: list[str]) -> list[str]:
    """Deduplicate (near-copies keep the earlier one) and fit the count and the character budget, dropping the
    oldest first."""
    unique: list[str] = []
    for text in (t.strip() for t in invariants if str(t).strip()):
        if not any(_similarity(text, kept) >= 0.6 for kept in unique):
            unique.append(text)
    while unique and (len(unique) > MAX_INVARIANTS or sum(len(t) for t in unique) > MAX_INVARIANTS_CHARS):
        unique.pop(0)
    return unique


def consolidate_agent_prompt(
    agent_md_path: str | Path,
    failure_ledger_path: str | Path = "state/failure_ledger.json",
    provider: str | None = None,
) -> dict[str, Any]:
    """Rewrite the whole learned section of an agent's prompt when the raw rules reach the threshold: the
    invariants it already has plus the new rules become one short list within a fixed budget. Nothing is
    appended to a growing tail (2026-11-13: nine near-identical invariants and nine empty epoch lines)."""
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
        return {"status": "no_op", "agent": path.stem, "file": str(path), "rules_consolidated": 0}

    ledger_file = resolve_adk_path(failure_ledger_path)
    ledger_data = read_json_state(ledger_file) if ledger_file.exists() else {"failures": []}
    kept_rules, dropped = _effective_rules(raw_rules, ledger_data, path.stem)
    existing_invariants = _extract_existing_invariants(base_part)
    consolidator_md = resolve_adk_path("agents/evolution/prompt_consolidator.md")

    invariants: list[str] | None = None
    if consolidator_md.exists() and kept_rules:
        llm_res = call_agent(
            consolidator_md,
            {
                "agent_id": path.stem,
                "base_prompt": base_part.split(CONSOLIDATED_HEADER, 1)[0].strip(),
                "accumulated_rules": kept_rules,
                "existing_consolidated_invariants": existing_invariants,
                "budget": {"max_invariants": MAX_INVARIANTS, "max_chars": MAX_INVARIANTS_CHARS},
            },
            model_tier="LRM",
            provider=provider,
        )["output"]
        if isinstance(llm_res, dict):
            proposed = llm_res.get("invariants")
            if isinstance(proposed, list) and all(isinstance(t, str) for t in proposed) and proposed:
                invariants = [str(t) for t in proposed]
            elif llm_res.get("consolidated_invariant"):
                invariants = existing_invariants + [str(llm_res["consolidated_invariant"]).strip()]
    if invariants is None:
        invariants = existing_invariants + ([" | ".join(dict.fromkeys(kept_rules))] if kept_rules else [])
    invariants = _fit_invariants(invariants)

    base_before = base_part.split(CONSOLIDATED_HEADER, 1)[0].rstrip()
    base_before = re.sub(r"\n-{3,}\s*$", "", base_before).rstrip()
    section = "\n".join(f"- **INVARIANT**: {text}" for text in invariants)
    new_full_content = f"{base_before}\n\n---\n\n{CONSOLIDATED_HEADER}\n{section}\n\n{LEARNED_HEADER}\n"
    path.write_text(new_full_content, encoding="utf-8")

    cycle_num = len(ledger_data.get("compactions", [])) + 1
    ledger_data.setdefault("compactions", []).append(
        {
            "agent": path.stem,
            "cycle": cycle_num,
            "rules_consolidated_count": len(raw_rules),
            "consolidated_rules": raw_rules,
            "dropped_ineffective": dropped,
            "invariants": invariants,
        }
    )
    write_json_state(ledger_file, ledger_data)

    return {
        "status": "consolidated",
        "agent": path.stem,
        "file": str(path),
        "cycle": cycle_num,
        "rules_consolidated": len(raw_rules),
        "dropped_ineffective": [d["rule"] for d in dropped],
        "invariants": invariants,
    }


def mutate_agent_prompt(
    agent_md_path: str | Path,
    new_rule: str,
    failure_context: str | None = None,
    failure_ledger_path: str | Path = "state/failure_ledger.json",
    compaction_threshold: int = DEFAULT_COMPACTION_THRESHOLD,
    provider: str | None = None,
    category: str = "",
    cycle: int = 0,
) -> dict[str, Any]:
    """Append a learned rule to an agent's .md file (blocking rigid GUARDs) and rewrite the learned section every
    `compaction_threshold` (4) rules. `category` and `cycle` let the consolidation judge the rule's effect."""
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
    ledger_data.setdefault("rules", []).append(
        {"agent": path.stem, "rule": new_rule.strip(), "category": category, "cycle": int(cycle)}
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

    # Count accumulated raw rules under LEARNED_HEADER; rewrite the learned section every `compaction_threshold` rules
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
