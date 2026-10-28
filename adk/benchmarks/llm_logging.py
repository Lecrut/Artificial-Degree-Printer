from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _map_agent_layer(agent_stem: str) -> str:
    """Return the architecture layer associated with an agent."""
    name = agent_stem.lower()
    if "redteam" in name or "auditor" in name or "verifier" in name:
        return "Warstwa 3 (Weryfikacja / Bramki Jakości)"
    if "planner" in name or "hitl" in name:
        return "Warstwa 1 (Planowanie / Gate HITL)"
    if "guard" in name or "critic" in name:
        # Ogólne guardy/krytycy jeśli nie redteam
        return "Warstwa 1 (Planowanie / Gate HITL)"
    if "coder" in name or "tester" in name or "writer" in name or "researcher" in name or "specialist" in name:
        return "Warstwa 2 (Generatory Artefaktów)"
    if "evolution" in name or "architect" in name or "consolidator" in name:
        return "Warstwa 4 (Autonomiczna Samoewolucja)"
    return "Agent Specjalistyczny"


def export_task_llm_interactions(
    output_dir: Path | str,
    interactions: list[dict[str, Any]],
    task_id: str,
    title_pl: str,
    domain: str,
    provider: str,
    lrm_model: str,
    sml_model: str,
) -> dict[str, str]:
    """Export complete record of LLM prompts, payloads, decisions, and raw responses to Markdown and JSONL.

    Creates:
      - llm_interactions.md: A human-readable Markdown log with summary table and collapsible prompts/responses.
      - llm_interactions.jsonl: Line-delimited JSON containing exact full prompt and response payloads.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    jsonl_file = out_path / "llm_interactions.jsonl"
    md_file = out_path / "llm_interactions.md"

    # 1. Write structured JSONL
    with jsonl_file.open("w", encoding="utf-8") as f:
        for item in interactions:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # 2. Write readable Markdown report
    total_calls = len(interactions)
    total_time_ms = sum(float(i.get("elapsed_ms", 0.0)) for i in interactions)
    live_calls = sum(1 for i in interactions if i.get("provider") in ("google", "ollama"))

    md_lines: list[str] = [
        f"# Ślad Decyzji i Promptów LLM – [{task_id}] {title_pl}",
        "",
        f"- **Domena:** {domain}",
        f"- **Dostawca LLM:** `{provider.upper()}` (Modele: LRM=`{lrm_model}`, SML=`{sml_model}`)",
        f"- **Liczba zapytań LLM:** {total_calls} (w tym zapytań sieciowych API: {live_calls})",
        f"- **Łączny czas inferencji:** {total_time_ms / 1000.0:.2f} s ({total_time_ms:.1f} ms)",
        "",
        "Dokument zawiera pełny zapis wszystkich zapytań skierowanych do modeli LLM w trakcie realizacji zadania benchmarkowego,",
        "w tym dokładne prompty systemowe, przekazane dane (JSON payload), podjęte decyzje i surowe odpowiedzi modeli.",
        "",
        "---",
        "",
        "## 📋 Tabela Podsumowująca Podjęte Decyzje",
        "",
        "| Krok | Agent | Warstwa Architektury | Model (Tier) | Czas | Podjęta Decyzja / Działanie |",
        "|:---:|:---|:---|:---|:---:|:---|",
    ]

    for item in interactions:
        step = item.get("step_index", item.get("step", 1))
        agent = item.get("agent", "unknown")
        layer = _map_agent_layer(agent)
        model = f"{item.get('model_name', 'model')} ({item.get('model_tier', 'SML')})"
        t_ms = f"{item.get('elapsed_ms', 0):.0f} ms"
        dec = str(item.get("decision_summary", "Wykonano zadanie")).replace("|", "\\|")
        md_lines.append(f"| {step} | `{agent}` | {layer} | {model} | {t_ms} | {dec} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 🔍 Szczegółowy Zapis Promptów i Odpowiedzi Krok po Kroku",
        "",
    ])

    for item in interactions:
        step = item.get("step_index", item.get("step", 1))
        agent = item.get("agent", "unknown")
        layer = _map_agent_layer(agent)
        provider_used = item.get("provider", provider)
        model_name = item.get("model_name", "unknown")
        model_tier = item.get("model_tier", "SML")
        elapsed_ms = item.get("elapsed_ms", 0.0)
        decision_summary = item.get("decision_summary", "")
        combined_prompt = str(item.get("combined_prompt", "")).strip()
        system_prompt = str(item.get("system_prompt", "")).strip()
        user_payload = item.get("user_payload", {})
        raw_response = str(item.get("raw_response", "")).strip()
        parsed_output = item.get("parsed_output", {})

        payload_json = json.dumps(user_payload, ensure_ascii=False, indent=2)
        parsed_json = json.dumps(parsed_output, ensure_ascii=False, indent=2)

        md_lines.extend([
            f"### Krok {step}: Agent `{agent}`",
            "",
            f"- **Warstwa:** {layer}",
            f"- **Dostawca / Model:** `{provider_used}` / `{model_name}` ({model_tier})",
            f"- **Czas wykonania:** {elapsed_ms:.1f} ms",
            f"- **Kluczowa decyzja:** **{decision_summary}**",
            "",
            "<details>",
            f"<summary><b>📥 Prompt wysłany do LLM (System Prompt + JSON Payload) — {len(combined_prompt)} znaków [Kliknij, aby rozwinąć]</b></summary>",
            "",
            "#### Instrukcja Systemowa Agenta:",
            "```markdown",
            system_prompt,
            "```",
            "",
            "#### Przekazany Payload Danych (Input JSON):",
            "```json",
            payload_json,
            "```",
            "",
            "</details>",
            "",
            "<details open>",
            "<summary><b>📤 Odpowiedź zwrócona przez LLM (Decyzja / Wygenerowany JSON) [Kliknij, aby zwinąć]</b></summary>",
            "",
            "```json",
            parsed_json if parsed_output else raw_response,
            "```",
            "",
            "</details>",
            "",
            "---",
            "",
        ])

    md_file.write_text("\n".join(md_lines), encoding="utf-8")

    return {
        "md_path": str(md_file),
        "jsonl_path": str(jsonl_file),
    }

