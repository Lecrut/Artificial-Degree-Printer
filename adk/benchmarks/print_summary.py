from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def extract_step_prompt_context(ix: dict[str, Any]) -> str:
    payload = ix.get("user_payload") or {}
    if not isinstance(payload, dict):
        return str(payload)[:200]

    # 1. Task builder step (seed_coder, seed_tester, sota_researcher, seed_writer)
    if "task" in payload and isinstance(payload["task"], dict):
        t = payload["task"]
        tid = t.get("task_id", "?")
        desc = t.get("description", "")
        tfile = payload.get("target_file") or t.get("target_node", "")
        return f"Zadanie {tid} [{tfile}]: {desc}"

    # 2. Remediation planner step
    if "failed_task" in payload and isinstance(payload["failed_task"], dict):
        ft = payload["failed_task"]
        err_rep = payload.get("error_report") or {}
        issues = err_rep.get("issues") or []
        first_issue = issues[0] if issues else "brak szczegółów"
        return f"Naprawa zadania {ft.get('task_id')} ({ft.get('assigned_agent')}) | Błąd: {str(first_issue)[:160]}"

    # 3. Evolution architect step
    if "failed_agent" in payload:
        fa = payload.get("failed_agent")
        cnt = payload.get("agent_failure_count", 1)
        tid = payload.get("task_id", "?")
        vrep = payload.get("validation_report") or {}
        issues = vrep.get("issues") or []
        first_issue = issues[0] if issues else "błąd walidacji W3"
        return f"Analiza awarii agenta '{fa}' (próba #{cnt} w zadaniu {tid}) | Powód: {str(first_issue)[:160]}"

    # 4. Mutate agent prompt consolidation
    if "rules" in payload and "agent_name" in payload:
        return f"Konsolidacja {len(payload['rules'])} reguł ewolucyjnych dla agenta '{payload['agent_name']}'"

    # 5. Verification auditors (code_auditor, symbolic_auditor, redteam_critic_guard)
    if "test_report" in payload:
        tr = payload["test_report"] or {}
        errs = payload.get("issues") or tr.get("errors") or []
        return f"Audyt kodu (pytest={tr.get('pytest_passed')}, ruff={tr.get('ruff_passed')}, błędy={len(errs)})"

    if "symbolic_reports" in payload:
        errs = payload.get("issues") or []
        return f"Audyt symboliczny (błędy referencji={len(errs)})"

    if "code_audit" in payload and "symbolic_audit" in payload:
        errs = payload.get("issues") or []
        return f"Bramka obrony Red-Team (łączna liczba zastrzeżeń={len(errs)})"

    # 6. Task Critic Guard
    if "tasks" in payload and isinstance(payload["tasks"], list):
        t_ids = [str(x.get("task_id", "?")) for x in payload["tasks"] if isinstance(x, dict)]
        return f"Walidacja planu zadań: [{', '.join(t_ids)}]"

    # 7. Initial Task Planner
    if "user_prompt" in payload:
        return f"Prompt główny: {payload['user_prompt']}"

    # Fallback if already slimmed
    if "prompt" in ix:
        return str(ix["prompt"])

    return str(list(payload.keys()))


def build_slim_step(ix: dict[str, Any]) -> dict[str, Any]:
    if "step" in ix and "prompt" in ix and "decision" in ix:
        return ix
    return {
        "step": ix.get("step_index"),
        "agent": ix.get("agent"),
        "model": f"{ix.get('model_name')} ({ix.get('model_tier')})",
        "elapsed_s": round(float(ix.get("elapsed_ms", 0.0)) / 1000.0, 2),
        "prompt": extract_step_prompt_context(ix),
        "decision": ix.get("decision_summary", ""),
    }


def slim_summary_json_in_place(summary_path: Path) -> dict[str, Any]:
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    for task in data.get("tasks", []):
        tel = task.get("llm_telemetry") or {}
        interactions = tel.get("interactions") or task.get("steps") or []

        if not task.get("prompt") or task.get("prompt") == "Brak":
            for ix in interactions:
                p0 = ix.get("user_payload") or {}
                if isinstance(p0, dict) and p0.get("user_prompt"):
                    task["prompt"] = str(p0["user_prompt"])
                    break
                if str(ix.get("prompt", "")).startswith("Prompt główny: "):
                    task["prompt"] = str(ix["prompt"]).replace("Prompt główny: ", "", 1)
                    break

        slim_steps = [build_slim_step(ix) for ix in interactions]
        task["steps"] = slim_steps

        if "interactions" in tel:
            del tel["interactions"]
        if "call_log" in tel:
            del tel["call_log"]
        if "decisions" in task:
            del task["decisions"]

    summary_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def format_benchmark_markdown(data: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("# Raport Przebiegu Benchmarków ADK (Prompty i Kroki Agentów)")
    lines.append("")
    lines.append(
        f"- **Provider**: `{data.get('provider')}` | **LRM**: `{data.get('lrm_model')}` | **SML**: `{data.get('sml_model')}`"
    )
    lines.append(
        f"- **Całkowity czas**: `{data.get('total_elapsed_seconds', 0):.1f} s` "
        f"(`{data.get('total_elapsed_seconds', 0) / 60:.1f} min`) | "
        f"**Łączna liczba kroków LLM**: `{data.get('total_llm_calls')}`"
    )
    lines.append("")
    lines.append("## Spis zadań")
    for idx, task in enumerate(data.get("tasks", []), 1):
        tid = task.get("task_id")
        title_pl = task.get("title_pl")
        status = task.get("orchestrator_status")
        steps_cnt = len(task.get("steps") or [])
        lines.append(f"{idx}. **[{tid}](#{tid})** — {title_pl} (`{status}`, {steps_cnt} kroków)")
    lines.append("")

    for task in data.get("tasks", []):
        tid = task.get("task_id")
        title_pl = task.get("title_pl")
        status = task.get("orchestrator_status")
        replans = task.get("replan_count")
        tel = task.get("llm_telemetry") or {}
        steps = task.get("steps") or []
        main_prompt = task.get("prompt", "Brak")

        lines.append("---")
        lines.append("")
        lines.append(f"## <a id=\"{tid}\"></a>`{tid}` — {title_pl}")
        lines.append("")
        lines.append(
            f"- **Status końcowy**: `{status}` | **Pętle naprawcze (replan)**: `{replans}` | "
            f"**Kroki LLM**: `{len(steps)}` | **Czas inferencji**: `{tel.get('total_inference_ms', 0) / 1000:.1f} s`"
        )
        lines.append("")
        lines.append("### Prompt zadania")
        lines.append("```text")
        lines.append(main_prompt)
        lines.append("```")
        lines.append("")

        cycles = task.get("architecture_cycles") or []
        if cycles:
            lines.append("### Cykle samonaprawy (`W2 -> W3 -> W4 -> W1 -> W2 -> W3`)")
            lines.append("| Cykl | Zadanie | Węzeł | Agent | W3 (Start) | Akcja W4 | Zadanie naprawcze W1 | W3 (Po naprawie) |")
            lines.append("|:---:|:---:|:---:|---|:---:|:---:|:---:|:---:|")
            for c in cycles:
                lines.append(
                    f"| #{c.get('cycle_number')} | `{c.get('task_id')}` | `{c.get('node_id')}` | "
                    f"`{c.get('failed_agent')}` | `{c.get('w3_initial_status')}` | `{c.get('w4_action')}` | "
                    f"`{c.get('w1_remediation_task_id')}` | **`{c.get('w3_post_remediation_status')}`** |"
                )
            lines.append("")

        lines.append("### Kroki wykonania (chronologicznie)")
        lines.append("")
        for st in steps:
            s_idx = st.get("step") or 0
            agent = st.get("agent", "")
            model = st.get("model", "")
            sec = st.get("elapsed_s", 0.0)
            prm = st.get("prompt", "")
            dec = st.get("decision", "")

            lines.append(f"#### Krok `{s_idx:02d}` — `{agent}` ({model}, `{sec:.1f}s`)")
            lines.append(f"- **Prompt / Wejście**: {prm}")
            lines.append(f"- **Decyzja / Wyjście**: {dec}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    summary_file = repo_root / "benchmarks" / "benchmark_summary.json"
    ws_summary_file = repo_root / "adk" / "workspace" / "benchmarks" / "benchmark_summary.json"

    cleaned_data = slim_summary_json_in_place(summary_file)
    if ws_summary_file.exists():
        slim_summary_json_in_place(ws_summary_file)

    report_md = format_benchmark_markdown(cleaned_data)
    out_md = repo_root / "benchmarks" / "benchmark_steps.md"
    out_md.write_text(report_md, encoding="utf-8")

    # Remove old .txt file if present
    old_txt = repo_root / "benchmarks" / "READABLE_BENCHMARK_STEPS.txt"
    if old_txt.exists():
        old_txt.unlink()

    print(f"Zapisano czytelny raport Markdown do: {out_md}")
